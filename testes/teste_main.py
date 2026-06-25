import os
import time
import json
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Módulos
from testes.teste_ligas import TESTE_COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes 
import odds, bingo357
from telegram import menus

# Funções de raspagem
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
from funcoes.raspagem_scouts import pegar_scouts_avancados

def enviar_telegram(mensagem, chat_id_destino):
    token = os.getenv('TELEGRAM_TOKEN')
    if not token or not chat_id_destino:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id_destino, 
            "text": mensagem,  # <--- Corrigido de 'message' para 'mensagem'
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"Erro Telegram: {e}")


def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver
                            
def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    jogos_para_pendentes = []  
    total_mercados = 0 

    try:
        for nome_comp, url in TESTE_COMPETICOES.items():
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
                    try:
                        tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                        tempo_raw = tempo_el.text.strip()
                    except Exception:
                        continue

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
                        for rg in res_gols:
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # 2. Ambas Marcam
                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts:
                            mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        # 3. Chance Dupla
                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        for rc in res_cd:
                            tipo_cd = "1X" if "1X" in rc else "X2"
                            mercados_para_processar.append({"texto": rc, "chave": tipo_cd})

                        # 4. Vitória Casa
                        res_vc = vitoria_casa.verificar_vitoria_casa(s)
                        for rv in res_vc:
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # 5. Processamento Jogadores
                        res_jogadores = jogadores.verificar_destaques_jogadores(s.get("historico_chutes", {}), 3, nome_comp)
                        for rj in res_jogadores:
                            mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                        # 6. Mercado de Cartões
                        # Hack: Forçamos o nome da liga para o formato que o cartoes.py aceita (Mundo - Copa do Mundo)
                        liga_cartoes = "Mundo - Copa do Mundo" if nome_comp == "Copa do Mundo" else nome_comp
                        
                        res_cartoes = cartoes.analisar_dados_cartoes(
                            s.get("historico_mandante_am", {}), 
                            s.get("historico_mandante_vm", {}), 
                            s.get("historico_visitante_am", {}), 
                            s.get("historico_visitante_vm", {}), 
                            liga_cartoes, 
                            3
                        )
                        
                        if res_cartoes.get("aprovado"):
                            media = res_cartoes.get('media_confronto', 0)
                            if media >= 4.0: m_fmt = "Cartões Totais: +3.5"
                            elif media >= 3.0: m_fmt = "Cartões Totais: +2.5"
                            elif media >= 2.0: m_fmt = "Cartões Totais: +1.5"
                            elif media >= 1.0: m_fmt = "Cartões Totais: -3.5"
                            else: m_fmt = "Cartões Totais: -2.5"
                            mercados_para_processar.append({"texto": m_fmt, "chave": "CARTOES_CONFRONTO"})
                            

                        
                        # --- VALIDAÇÃO DE ODDS E FILTRAGEM ---
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                m_texto, m_chave = item["texto"], item["chave"]
                                valor_odd_str = "1.50" if m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else v_odds.get(m_chave, "N/A")
                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    if odd_float >= 1.25:
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m_texto, "odd": valor_odd_str if m_chave not in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else "Análise", "liga": nome_comp,
                                            "link_betano": s.get("link_betano")
                                        })
                                        jogos_para_pendentes.append({
                                            "time_casa": t1, "time_fora": t2, "mercado": m_texto,
                                            "mercado_ranking": m_texto.upper(),
                                            "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                        })
                                        total_mercados += 1
                                except ValueError: continue
                except Exception as e:
                    print(f"⚠️ Erro ao processar partida: {e}")
                    continue

        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            cache_dados = {}
            for j in lista_para_filtros:
                chave = f"{str(j.get('time_casa')).strip().lower()}x{str(j.get('time_fora')).strip().lower()}"
                cache_dados[chave] = {"link_betano": j.get("link_betano"), "liga": j.get("liga"), "horario": j.get("horario"), "odd": j.get("odd")}
            for j in jogos_para_pendentes:
                chave = f"{str(j.get('time_casa')).strip().lower()}x{str(j.get('time_fora')).strip().lower()}"
                if chave in cache_dados: cache_dados[chave]["link_h2h"] = j.get("link_h2h")

            canal_id = os.getenv('CHANNEL_ID')
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros, qtd_alvo=5, estrategia="ACERTOS", modo_elite=True)
            texto_bingos_final = bingo357.formatar_para_telegram(novos_bilhetes, cache_dados, aviso_menu="💰 *MENU DE BINGOS (TESTE)*")
            if texto_bingos_final and canal_id:
                menus.enviar_menu_bingo(canal_id, "💰 *MENU DE BINGOS*\n\n" + texto_bingos_final)

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try: driver.quit()
        except: pass
                        

if __name__ == "__main__":
    main()
