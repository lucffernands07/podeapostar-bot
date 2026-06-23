import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Importações dos seus módulos
from testes.teste_ligas import TESTE_COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes
import odds
import bingo357

# Importações das funções de raspagem
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
from funcoes.raspagem_scouts import pegar_scouts_avancados

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    # Adicione estas linhas para igualar ao principal:
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) # Aumenta a tolerância para o site carregar
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    jogos_para_pendentes = []  
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: 
                break 
            print(f"\n--- Analisando: {nome_comp} ---")
            
            try:
                driver.get(url)
                time.sleep(4)
                elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            except Exception as e:
                if "invalid session id" in str(e).lower() or "session" in str(e).lower():
                    print("⚠️ Sessão do Chrome caiu! Reiniciando o navegador para continuar...")
                    try: driver.quit()
                    except: pass
                    driver = configurar_driver() 
                    driver.get(url)
                    time.sleep(4)
                    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                else:
                    print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                    continue
            
            for el in elementos:
                try:
                    # 1. Tenta capturar o elemento de tempo de forma isolada e segura
                    try:
                        tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                        tempo_raw = tempo_el.text.strip()
                    except Exception:
                        # Se o elemento sumiu (jogo ao vivo, encerrado, etc.), passa para o próximo sem estourar o log
                        continue

                    # 2. Verifica se o texto é uma string de status/tempo extra em vez de horário válido
                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                        continue

                    # 3. Pega a última parte do texto do tempo para converter
                    partes_tempo = tempo_raw.split()
                    if not partes_tempo:
                        continue
                        
                    horario_str = partes_tempo[-1]
                    
                    # Garante que temos um formato de hora válido antes de fazer o strptime
                    if ":" not in horario_str:
                        continue

                    h_obj = datetime.strptime(horario_str, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        
                        url_h2h_final = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        
                        # EXECUÇÃO SEQUENCIAL DA RASPAGEM 1 E RASPAGEM 2
                        s_inicial = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        s = pegar_scouts_avancados(driver, s_inicial, t1, t2)
                        
                        mercados_para_processar = []

                        # 1. Gols
                        res_gols = gols.verificar_gols(s)
                        for rg in res_gols:
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # 2. Ambas Marcam
                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts:
                            mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        # 3. Chance Dupla
                        if s.get("casa_vitorias_recente", 0) >= 4 or s.get("fora_vitorias_recente", 0) >= 4:
                            s["chance_dupla_pct"] = "100%"
                        elif s.get("casa_vitorias_recente", 0) == 3 or s.get("fora_vitorias_recente", 0) == 3:
                            s["chance_dupla_pct"] = "90%"
                        else:
                            s["chance_dupla_pct"] = "80%"

                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        for rc in res_cd:
                            tipo_cd = "1X" if "1X" in rc else "X2"
                            mercados_para_processar.append({"texto": rc, "chave": tipo_cd})

                        # 4. Vitória Casa
                        res_vc = vitoria_casa.verificar_vitoria_casa(s)
                        for rv in res_vc:
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # 5. Processamento Jogadores
                        try:
                            if 'joggers' in globals():
                                res_jogadores = joggers.verificar_destaques_jogadores(
                                    historico_chutes=s.get("historico_chutes", {}),
                                    quantidade_jogos=3,
                                    nome_liga=nome_comp
                                )
                            else:
                                res_jogadores = jogadores.verificar_destaques_jogadores(
                                    historico_chutes=s.get("historico_chutes", {}),
                                    quantidade_jogos=3,
                                    nome_liga=nome_comp
                                )
                        except Exception as e_jog:
                            print(f"  ⚠️ Erro no módulo de jogadores: {e_jog}")
                            res_jogadores = []

                        for rj in res_jogadores:
                            mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                       # 6. Mercado de Cartões Coletivos
                        try:
                            res_cartoes = cartoes.analisar_dados_cartoes(
                                historico_mandante_am=s.get("historico_mandante_am", {}), 
                                historico_mandante_vm=s.get("historico_mandante_vm", {}),
                                historico_visitante_am=s.get("historico_visitante_am", {}), 
                                historico_visitante_vm=s.get("historico_visitante_vm", {}),
                                nome_liga=nome_comp,
                                quantidade_jogos=3
                            )
                        except Exception as e_cart:
                            print(f"  ⚠️ Erro no módulo de cartões: {e_cart}")
                            res_cartoes = {"aprovado": False}

                        if res_cartoes.get("aprovado"):
                            media = res_cartoes.get('media_confronto', 0)
                            
                            # 🎴 Tradução da média para mercados tradicionais da Betano
                            if media >= 4.0:
                                mercado_formatado = "Cartões Totais: +4.5"
                            elif media >= 3.0:
                                mercado_formatado = "Cartões Totais: +2.5"
                            elif media >= 2.0:
                                mercado_formatado = "Cartões Totais: +1.5"
                            elif media >= 1.0:
                                mercado_formatado = "Cartões Totais: -3.5"
                            else:
                                mercado_formatado = "Cartões Totais: -2.5"

                        # Validação de Odds e adição na lista_para_filtros
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                valor_odd_str = v_odds.get(item["chave"], "1.50")
                                if float(valor_odd_str.replace(',', '.')) >= 1.25:
                                    lista_para_filtros.append({"time_casa": t1, "time_fora": t2, "mercado": item["texto"], "odd": valor_odd_str, "liga": nome_comp})
                                    total_mercados += 1
                except Exception:
                    continue

        # --- PROCESSAMENTO FINAL (Fora do loop) ---
        if lista_para_filtros:
            print(f"\n🧪 TESTE: {len(lista_para_filtros)} mercados coletados.")
            bilhete_elite = bingo357.montar_bilhete_elite_main(lista_para_filtros)
            print(f"🧪 Teste Bingo Elite: {len(bilhete_elite) if bilhete_elite else 0} bilhetes.")
            novos_bingos = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            print(f"🧪 Teste Bingos Estratégicos: {len(novos_bingos) if novos_bingos else 0} conjuntos.")
        else:
            print("\n⚠️ Nenhum mercado passou nos filtros.")

    except Exception as e:
        print(f"❌ Erro Crítico no Teste: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
