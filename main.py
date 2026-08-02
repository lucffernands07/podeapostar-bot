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
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitorias, jogadores, cartoes, escanteios
import odds, bingo357
from telegram import menus

# Funções de raspagem
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
from funcoes.raspagem_scouts import pegar_scouts_avancados
from funcoes.raspagem_estatisticas import pegar_estatisticas_coletivas

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
    driver.set_page_load_timeout(15) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    hoje_no_site = hoje_ref.strftime("%d.%m.")
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
                time.sleep(3)  
                
                # 🟢 Rola a página até o fim para carregar jogos ocultos (Lazy Loading)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                if not elementos:
                    elementos = driver.find_elements(By.CSS_SELECTOR, "div[id^='g_1_']")
                
                print(f"📊 Total de elementos encontrados na página: {len(elementos)}")

            except Exception as e:
                if "invalid session id" in str(e).lower() or "session" in str(e).lower():
                    print("⚠️ Sessão do Chrome caiu! Reiniciando o navegador...")
                    try: driver.quit()
                    except: pass
                    driver = configurar_driver() 
                    driver.get(url)
                    time.sleep(3)
                    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                else:
                    print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                    continue
            
            aba_principal = driver.current_window_handle
            total_elementos = len(elementos)
            
            ids_jogos_salvos_pendentes = set()
            
            for idx in range(total_elementos):
                try:
                    elementos_vivos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                    if not elementos_vivos:
                        elementos_vivos = driver.find_elements(By.CSS_SELECTOR, "div[id^='g_1_']")
                    
                    if idx >= len(elementos_vivos):
                        break
                        
                    el = elementos_vivos[idx]
                    texto_bruto_jogo = el.text.replace('\n', ' | ').strip()
                    print(f"     🔹 Elemento [{idx+1}]: {texto_bruto_jogo}")

                    try:
                        tempo_el = el.find_element(By.CSS_SELECTOR, "span[class*='dateContent'], .event__stageTime, .event__time")
                        tempo_raw = tempo_el.text.strip()
                    except Exception:
                        print(f"      ⏩ Pulado: Não encontrou nenhum elemento de tempo.")
                        continue

                    if "Preview" in tempo_raw:
                        tempo_raw = tempo_raw.replace("Preview", "").strip()

                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                        print(f"      ⏩ Pulado: Status ao vivo/encerrado detectado ({tempo_raw})")
                        continue

                    partes_tempo = tempo_raw.split()
                    if not partes_tempo: continue

                    # Trata o horário UTC para jogos do dia
                    horario_str = partes_tempo[-1]
                    if ":" not in horario_str: continue

                    h_obj = datetime.strptime(horario_str, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        # Aceita os jogos da virada da noite (0, 1, 2, 3 UTC = 21h, 22h, 23h, 00h BR)
                        # E aceita os jogos do final do dia em UTC que vêm marcados como 'Amanhã' (21, 22, 23 UTC = 18h, 19h, 20h BR)
                        if h_obj.hour <= 3 or h_obj.hour >= 21: 
                            aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: 
                            aceitar = True

                    if aceitar:
                        print(f"      ⏰ Horário UTC: {horario_str} | Horário BR: {h_br} | Janela Aceita? {aceitar}")
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        if len(times) < 2:
                            print(f"      ⚠️ Falha: Não conseguiu ler os nomes dos dois times no elemento.")
                            continue
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        #-----------------------------------
                        id_jogo = None
                        try:
                            link_el = el.find_element(By.CSS_SELECTOR, "a.icon--preview")
                            url_jogo = link_el.get_attribute('href')
                            if "mid=" in url_jogo:
                                id_jogo = url_jogo.split("mid=")[-1].split("&")[0]
                        except Exception:
                            pass
    
                        if not id_jogo:
                            try:
                                link_el = el.find_element(By.CSS_SELECTOR, "a.eventRowLink")
                                id_jogo = link_el.get_attribute('id').split('_')[-1]
                            except Exception:
                                try:
                                    id_jogo = el.get_attribute('id').split('_')[-1]
                                except Exception:
                                    continue

                        if not id_jogo or len(id_jogo) < 3:
                            print(f"      ⚠️ Falha: ID do jogo inválido ou não encontrado.")
                            continue

                        print(f"      ✅ JOGO QUALIFICADO: {t1} x {t2} (ID: {id_jogo}) - Iniciando pipeline de análise...")

                        # ----------------------------------------------------------
                        # FASE 1: ANÁLISE DE MERCADOS DE RECORRÊNCIA (CASA / FORA)
                        # ----------------------------------------------------------
                        url_jogo_base = f"https://www.flashscore.com.br/jogo/{id_jogo}"
                        dados_jogo = pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2)
                        
                        if isinstance(dados_jogo, dict) and "url_h2h_base" not in dados_jogo:
                            dados_jogo["url_h2h_base"] = f"{url_jogo_base}/h2h"

                        mercados_fase1 = []

                        # 1. Gols
                        res_gols = gols.verificar_gols(dados_jogo)
                        for rg in res_gols:
                            if isinstance(rg, dict):
                                mercados_fase1.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # 2. Ambos Marcam
                        res_btts = ambos_marcam.verificar_btts(dados_jogo, mercados_gols_aprovados=res_gols)
                        for rb in res_btts:
                            if isinstance(rb, dict):
                                m_texto = rb.get("mercado", "")
                                m_tipo = rb.get("tipo", "BTTS")
                                mercados_fase1.append({"texto": m_texto, "chave": m_tipo})
                            elif isinstance(rb, str):
                                chave_btts = "BTTS_NAO" if "Não" in rb or "Nao" in rb else "BTTS"
                                mercados_fase1.append({"texto": rb, "chave": chave_btts})

                        # 3. Chance Dupla
                        res_cd = chance_dupla.verificar_chance_dupla(dados_jogo)
                        for rc in res_cd:
                            texto_cd = rc if isinstance(rc, str) else rc.get("mercado", "")
                            tipo_cd = "1X" if "1X" in texto_cd else "X2"
                            mercados_fase1.append({"texto": texto_cd, "chave": tipo_cd})

                        # 4. Vitória Casa / Vitória Fora
                        res_vitorias = vitorias.verificar_vitorias(dados_jogo)
                        for rv in res_vitorias:
                            texto_vic = rv if isinstance(rv, str) else rv.get("mercado", "")
                            chave_vic = "VITORIA_FORA" if "Fora" in texto_vic else "VITORIA_CASA"
                            mercados_fase1.append({"texto": texto_vic, "chave": chave_vic})

                        # Extração de Odds
                        v_odds = {}
                        if mercados_fase1:
                            try:
                                v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            except Exception as e_odds:
                                print(f"      ⚠️ Erro ao capturar odds da Fase 1: {e_odds}")
                                if "invalid session id" in str(e_odds).lower() or "session" in str(e_odds).lower():
                                    try: driver.quit()
                                    except: pass
                                    driver = configurar_driver()

                        mercados_para_processar = []

                        for item in mercados_fase1:
                            m_texto, m_chave = item["texto"], item["chave"]
                            valor_odd_str = v_odds.get(m_chave, "1.30")
                            
                            try:
                                odd_float = float(str(valor_odd_str).replace(',', '.'))
                                if odd_float >= 1.10:
                                    if "M45" in m_chave and odd_float >= 4.0: continue
                                    mercados_para_processar.append({"texto": m_texto, "chave": m_chave, "odd": str(odd_float)})
                                else:
                                    print(f"      ⚠️ Descartado (Odd baixa): {m_texto} | Valor: {valor_odd_str}")
                            except Exception as e_conv:
                                print(f"      ⚠️ Erro ao converter odd para float ({m_texto}): {e_conv}")
    
                        # ----------------------------------------------------------
                        # FASE 2: RASPAGEM DE ESTATÍSTICAS COLETIVAS
                        # ----------------------------------------------------------
                        print(f"      📊 [FASE 2] Buscando Estatísticas Coletivas (Escanteios/Cartões)...")
                        try:
                            driver.get(dados_jogo["url_h2h_base"])
                            time.sleep(1.5)
                            
                            dados_coletivos = pegar_estatisticas_coletivas(driver, dados_jogo)
                            if dados_coletivos and isinstance(dados_coletivos, dict):
                                dados_jogo.update(dados_coletivos)
                        except Exception as e_f2:
                            print(f"      ⚠️ Erro na Fase 2: {e_f2}")
                            if "invalid session id" in str(e_f2).lower() or "session" in str(e_f2).lower():
                                print("      🔄 Recuperando driver após queda na Fase 2...")
                                try: driver.quit()
                                except: pass
                                driver = configurar_driver()

                        res_escanteios = escanteios.analisar_dados_escanteios(
                            dados_jogo.get("cantos_mandante_h2h", []), 
                            dados_jogo.get("cantos_visitante_h2h", []), 
                            nome_comp, 
                            3
                        )
                        if res_escanteios and res_escanteios.get("aprovado"):
                            mercado_cantos_formatado = res_escanteios.get("mercado")
                            if mercado_cantos_formatado:
                                mercados_para_processar.append({"texto": mercado_cantos_formatado, "chave": "CANTOS_MEDIA", "odd": "1.30"})

                        res_cartoes = cartoes.analisar_dados_cartoes(
                            dados_jogo.get("cartoes_mandante_h2h", []),
                            dados_jogo.get("cartoes_visitante_h2h", []),
                            nome_comp,
                            3
                        )
                        if res_cartoes and res_cartoes.get("aprovado"):
                            mercado_cartoes_formatado = res_cartoes.get("mercado")
                            if mercado_cartoes_formatado:
                                mercados_para_processar.append({"texto": mercado_cartoes_formatado, "chave": "CARTOES_CONFRONTO", "odd": "1.30"})

                        # ----------------------------------------------------------
                        # FASE 3: RASPAGEM DE SCOUTS (JOGADORES)
                        # ----------------------------------------------------------
                        permite_jogadores = jogadores.validar_liga_para_jogadores(nome_comp)

                        if permite_jogadores:
                            try:
                                _ = driver.current_window_handle
                            except Exception:
                                try: driver.quit()
                                except: pass
                                driver = configurar_driver()

                            acumulador_scouts = {}
                            try:
                                driver.get(dados_jogo["url_h2h_base"])
                                time.sleep(1.5) 
                                driver.execute_script("window.scrollTo(0, 300);")
                                acumulador_scouts = pegar_scouts_avancados(driver, dados_jogo, t1, t2)
                            except Exception as e_f3:
                                print(f"      ⚠️ Erro na Fase 3: {e_f3}")
                            
                            resultado_jogadores = jogadores.analisar_dados_jogadores(acumulador_scouts, t1, t2)

                            if resultado_jogadores.get("aprovado"):
                                for jk in resultado_jogadores.get("jogadores_qualificados", []):
                                    txt_mercado = f"{jk['mercado']}: {jk['jogador']} ({jk['time'][:3].upper()}) | Méd: {jk['media']:.1f}"
                                    mercados_para_processar.append({
                                        "texto": txt_mercado,
                                        "chave": "JOGADOR_SCOUT",
                                        "odd": "1.30"
                                    })

                        url_h2h_final = dados_jogo.get("url_h2h_base", f"https://www.flashscore.com.br/jogo/{id_jogo}/")

                        # ----------------------------------------------------------
                        # ALIMENTAÇÃO DA LISTA FINAL
                        # ----------------------------------------------------------
                        if mercados_para_processar:
                            if id_jogo not in ids_jogos_salvos_pendentes:
                                jogos_para_pendentes.append({
                                    "time_casa": t1, 
                                    "time_fora": t2, 
                                    "mercado": "MÚLTIPLOS",
                                    "mercado_ranking": "LISTÃO GERAL", 
                                    "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                })
                                ids_jogos_salvos_pendentes.add(id_jogo)

                            for item in mercados_para_processar:
                                m_texto, m_chave, m_odd = item["texto"], item["chave"], item["odd"]
                                texto_limpo = m_texto.strip()
                                texto_lower = texto_limpo.lower()
                                
                                if "0.0" in texto_limpo and any(t in texto_lower for t in ["chute", "falta"]):
                                    continue

                                eh_scout = (
                                    m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO", "CANTOS_MEDIA", "JOGADOR_SCOUT"] or
                                    any(term in texto_lower for term in ["chute", "falta", "cartã", "cartao", "escanteio", "cantos"])
                                )

                                odd_para_lista = "Análise" if eh_scout else m_odd

                                lista_para_filtros.append({
                                    "horario": h_br, "time_casa": t1, "time_fora": t2,
                                    "mercado": m_texto, "odd": odd_para_lista, "liga": nome_comp,
                                    "link_betano": dados_jogo.get("link_betano"),
                                    "link_h2h": url_h2h_final,
                                    "odds_todas": v_odds
                                })
                                total_mercados += 1

                        # 🟢 Recarrega a página da liga para que o Selenium encontre os próximos jogos no loop (idx)
                        try:
                            driver.get(url)
                            time.sleep(2.0)
                        except Exception as e_volta:
                            print(f"⚠️ Erro ao recarregar a liga: {e_volta}")

                except Exception as e_jogo:
                    print(f"      ⚠️ Erro ao processar o jogo índice {idx}: {e_jogo}")
                    continue


        # --- PROCESSAMENTO E ENVIO FINAL (FORA DOS LOOPS) ---
        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            meu_chat_id = os.getenv('CHAT_ID')
            if meu_chat_id:
                cabecalho = "🎫 *LISTA DE MERCADOS DO DIA*\n\n"
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
    
            cache_dados = {}
            for j in lista_para_filtros:
                chave = f"{j['time_casa']}x{j['time_fora']}".lower().strip()
                cache_dados[chave] = {
                    "link": j.get("link_betano"),
                    "liga": j.get("liga"),
                    "horario": j.get("horario"),
                    "odd": j.get("odd"),
                    "link_h2h": j.get("link_h2h"),
                    "odds_todas": j.get("odds_todas", {})
                }

            canal_id = os.getenv('CHANNEL_ID')
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            texto_bingos_final = bingo357.formatar_para_telegram(novos_bilhetes, cache_dados)
    
            if texto_bingos_final and canal_id:
                try:
                    msg_bingo_formatada = "💰 *MENU DE BINGOS*\n\n" + texto_bingos_final
                    menus.enviar_menu_bingo(canal_id, msg_bingo_formatada)
                    print("📢 Menu interativo enviado para o Canal.")
                except Exception as e:
                    print(f"⚠️ Erro ao enviar menu para o canal: {e}")

            os.makedirs("ranking", exist_ok=True)
            with open("ranking/pendentes.json", "w", encoding="utf-8") as f:
                json.dump({"data_geracao": hoje_ref.strftime("%Y-%m-%d"), "jogos": jogos_para_pendentes}, f, indent=4, ensure_ascii=False)
            
            os.makedirs("telegram", exist_ok=True)
            with open(f"telegram/jogos_{hoje_ref.strftime('%Y-%m-%d')}.json", "w", encoding="utf-8") as f:
                json.dump([
                    {
                        "horario": j.get("horario"), 
                        "liga": j.get("liga"), 
                        "time_casa": j.get("time_casa"), 
                        "time_fora": j.get("time_fora"), 
                        "mercado": j.get("mercado"), 
                        "odd": j.get("odd"), 
                        "link_betano": j.get("link_betano"),
                        "link_h2h": j.get("link_h2h")
                    } 
                    for j in lista_para_filtros
                ], f, indent=4, ensure_ascii=False)
        else:
            print("⚠️ Nenhuma partida qualificada entrou na 'lista_para_filtros' após varrer os elementos.")

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
