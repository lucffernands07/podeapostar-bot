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
            "text": mensagem,
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
        for nome_comp, url in TESTES_COMPETICOES.items():
            if total_mercados >= 200: 
                break 
            print(f"\n--- Analisando: {nome_comp} ---")
            
            try:
                driver.get(url)
                time.sleep(4)
                elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            except Exception as e:
                if "invalid session id" in str(e).lower() or "session" in str(e).lower():
                    print("⚠️ Sessão do Chrome caiu! Reiniciando o navegador...")
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

                        # Gols, BTTS, CD, Vitoria
                        res_gols = gols.verificar_gols(s)
                        for rg in res_gols:
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts:
                            mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        for rc in res_cd:
                            tipo_cd = "1X" if "1X" in rc else "X2"
                            mercados_para_processar.append({"texto": rc, "chave": tipo_cd})

                        res_vc = vitoria_casa.verificar_vitoria_casa(s)
                        for rv in res_vc:
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # Jogadores
                        res_jogadores = jogadores.verificar_destaques_jogadores(s.get("historico_chutes", {}), 3, nome_comp)
                        for rj in res_jogadores:
                            mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                        # Cartões
                        res_cartoes = cartoes.analisar_dados_cartoes(s.get("historico_mandante_am", {}), s.get("historico_mandante_vm", {}), s.get("historico_visitante_am", {}), s.get("historico_visitante_vm", {}), nome_comp, 3)
                        if res_cartoes.get("aprovado"):
                            media = res_cartoes.get('media_confronto', 0)
                            if media >= 4.0: mercado_formatado = "Cartões Totais: +3.5"
                            elif media >= 3.0: mercado_formatado = "Cartões Totais: +2.5"
                            elif media >= 2.0: mercado_formatado = "Cartões Totais: +1.5"
                            elif media >= 1.0: mercado_formatado = "Cartões Totais: -3.5"
                            else: mercado_formatado = "Cartões Totais: -2.5"
                            mercados_para_processar.append({"texto": mercado_formatado, "chave": "CARTOES_CONFRONTO"})

                        # --- VALIDAÇÃO DE ODDS ---
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            
                            for item in mercados_para_processar:
                                m_texto, m_chave = item["texto"], item["chave"]
                                valor_odd_str = "1.50" if m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else v_odds.get(m_chave, "N/A")

                                try:
                                    odd_float = float(str(valor_odd_str).replace(',', '.'))
                                except (ValueError, TypeError, AttributeError):
                                    print(f"⚠️ Descartado (Odd inválida): {m_texto} | Valor: {valor_odd_str}")
                                    continue 

                                if "M45" in m_chave and odd_float >= 4.0: continue 
                                if m_chave == "CARTOES_CONFRONTO" and "0.0" in m_texto: continue
                                if m_chave == "CHUTES_ALVO" and "0.0" in m_texto: continue

                                if odd_float >= 1.25:
                                    lista_para_filtros.append({
                                        "horario": h_br, "time_casa": t1, "time_fora": t2,
                                        "mercado": m_texto, "odd": valor_odd_str if m_chave not in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else "Análise", "liga": nome_comp,
                                        "link_betano": s.get("link_betano")
                                    })
                                    jogos_para_pendentes.append({
                                        "time_casa": t1, "time_fora": t2, "mercado": m_texto,
                                        "mercado_ranking": m_texto.upper(), "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                    })
                                    total_mercados += 1
                except Exception as e:
                    print(f"⚠️ Erro ao processar partida: {e}")
                    continue

        # --- PROCESSAMENTO E ENVIO FINAL ---
        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            # 1. ENVIO DO LISTÃO PARA VOCÊ
            meu_chat_id = os.getenv('CHAT_ID')
            if meu_chat_id:
                cabecalho = "🎫 *LISTA TESTE DE MERCADOS DO DIA*\n\n"
                corpo = ""
                for j in lista_para_filtros:
                    bloco = f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}\n\n------------------------------------\n\n"
                    
                    if len(cabecalho + corpo + bloco) > 4000:
                        enviar_telegram(cabecalho + corpo, meu_chat_id)
                        cabecalho = "🎫 *LISTA (Continuação)*\n\n"
                        corpo = bloco
                    else:
                        corpo += bloco
                
                enviar_telegram(cabecalho + corpo, meu_chat_id)
                print("📨 Listão enviado.")
    
            # Preparação comum de dados
            cache_dados = {}
            for j in lista_para_filtros:
                chave = f"{j['time_casa']}x{j['time_fora']}"
                cache_dados[chave] = {
                    "link": j.get("link_betano"),
                    "liga": j.get("liga"),
                    "horario": j.get("horario"),
                    "odd": j.get("odd"),
                    "link_h2h": j.get("link_h2h") # Agora ele pega o link que você inseriu no loop
                }

    
            # 2. ENVIO AUTOMÁTICO DO BINGO ELITE (Pulado para evitar erros)
            print("📢 Pulando envio do Elite conforme solicitado.")
    
            # 3. ENVIO DO MENU INTERATIVO (Para os botões do canal) DESATIVADO PARA TESTES
            
            # Gravação de arquivos
            os.makedirs("ranking", exist_ok=True)
            with open("ranking/pendentes.json", "w", encoding="utf-8") as f:
                json.dump({"data_geracao": hoje_ref.strftime("%Y-%m-%d"), "jogos": jogos_para_pendentes}, f, indent=4, ensure_ascii=False)
            
            os.makedirs("telegram", exist_ok=True)
            with open(f"telegram/jogos_{hoje_ref.strftime('%Y-%m-%d')}.json", "w", encoding="utf-8") as f:
                json.dump([{"horario": j.get("horario"), "liga": j.get("liga"), "time_casa": j.get("time_casa"), "time_fora": j.get("time_fora"), "mercado": j.get("mercado"), "odd": j.get("odd"), "link_betano": j.get("link_betano")} for j in lista_para_filtros], f, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
                
