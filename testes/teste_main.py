import os
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Importações dos seus módulos
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes 
import odds  
import bingo357  

# Configuração de Logs Locais
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/teste_processamento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
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
                    print("⚠️ Sessão do Chrome caiu! Reiniciando...")
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
                    tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                    tempo_raw = tempo_el.text.strip()
                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                        continue

                    partes_tempo = tempo_raw.split()
                    if not partes_tempo: continue
                    horario_str = partes_tempo[-1]
                    if ":" not in horario_str: continue

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
                        
                        s_inicial = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        s = pegar_scouts_avancados(driver, s_inicial, t1, t2)
                        
                        mercados_para_processar = []

                        # 1. Gols
                        res_gols = gols.verificar_gols(s)
                        for rg in res_gols: mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # 2. Ambas Marcam
                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts: mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        # 3. Chance Dupla
                        if s.get("casa_vitorias_recente", 0) >= 4 or s.get("fora_vitorias_recente", 0) >= 4: s["chance_dupla_pct"] = "100%"
                        elif s.get("casa_vitorias_recente", 0) == 3 or s.get("fora_vitorias_recente", 0) == 3: s["chance_dupla_pct"] = "90%"
                        else: s["chance_dupla_pct"] = "80%"
                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        for rc in res_cd: mercados_para_processar.append({"texto": rc, "chave": "1X" if "1X" in rc else "X2"})

                        # 4. Vitória Casa
                        res_vc = vitoria_casa.verificar_vitoria_casa(s)
                        for rv in res_vc: mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # 5. Jogadores
                        res_jogadores = jogadores.verificar_destaques_jogadores(historico_chutes=s.get("historico_chutes", {}), quantidade_jogos=3, nome_liga=nome_comp)
                        for rj in res_jogadores: mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                        # 6. Cartões
                        try:
                            res_cartoes = cartoes.analisar_dados_cartoes(s.get("historico_mandante_am", {}), s.get("historico_mandante_vm", {}), s.get("historico_visitante_am", {}), s.get("historico_visitante_vm", {}), nome_comp, 3)
                            if res_cartoes.get("aprovado"):
                                media = res_cartoes.get('media_confronto', 0)
                                mercado_formatado = f"Cartões Totais: {'+4.5' if media >= 4.0 else '+2.5' if media >= 3.0 else '+1.5' if media >= 2.0 else '-3.5' if media >= 1.0 else '-2.5'}"
                                mercados_para_processar.append({"texto": mercado_formatado, "chave": "CARTOES_CONFRONTO"})
                        except: pass

                        # --- Validação e Filtro ---
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                m_texto, m_chave = item["texto"], item["chave"]
                                valor_odd_str = v_odds.get(m_chave, "1.50") if m_chave not in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else "1.50"
                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    if odd_float >= 1.25:
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m_texto, "odd": valor_odd_str, "liga": nome_comp
                                        })
                                        total_mercados += 1
                                except ValueError: continue
                except Exception as e:
                    print(f"⚠️ Erro ao processar partida: {e}")
                    continue

        print(f"\n✅ Processamento concluído. {len(lista_para_filtros)} mercados encontrados em memória.")
    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
    
