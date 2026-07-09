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

# Módulos de Teste
from testes.teste_ligas import TESTE_COMPETICOES as COMPETICOES
from testes.teste_jogadores import LIGAS_ELITE_JOGADORES
from testes.teste_escanteios import analisar_dados_escanteios
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa
from testes import teste_jogadores as jogadores
import odds, bingo357
from telegram import menus

# Funções de raspagem
from testes.teste_raspagem_h2h import pegar_estatisticas_h2h
from testes.teste_raspagem_scouts import pegar_scouts_avancados
from testes.teste_raspagem_estatisticas import pegar_estatisticas_coletivas

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
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: 
                break 
            print(f"\n--- Analisando: {nome_comp} ---")
            
            try:
                driver.get(url)
                time.sleep(6)  
                
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
                    time.sleep(6)
                    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                else:
                    print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                    continue
            
            for idx, el in enumerate(elementos):
                try:
                    texto_bruto_jogo = el.text.replace('\n', ' | ').strip()
                    print(f"   🔹 Elemento [{idx+1}]: {texto_bruto_jogo}")

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
                        
                    horario_str = partes_tempo[-1]
                    if ":" not in horario_str: continue

                    h_obj = datetime.strptime(horario_str, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: aceitar = True

                    print(f"      ⏰ Horário UTC: {horario_str} | Horário BR: {h_br} | Janela Aceita? {aceitar}")

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        if len(times) < 2:
                            print(f"      ⚠️ Falha: Não conseguiu ler os nomes dos dois times no elemento.")
                            continue
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        
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
                        # FASE 1: RASPAGEM H2H E FILTRO DE MERCADOS PRINCIPAIS
                        # ----------------------------------------------------------
                        url_h2h_final = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        s_inicial = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
                        mercados_para_processar = []

                        # Gols, BTTS, CD, Vitoria
                        res_gols = gols.verificar_gols(s_inicial)
                        for rg in res_gols:
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        res_btts = ambos_marcam.verificar_btts(s_inicial)
                        if res_btts:
                            mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        res_cd = chance_dupla.verificar_chance_dupla(s_inicial)
                        for rc in res_cd:
                            tipo_cd = "1X" if "1X" in rc else "X2"
                            mercados_para_processar.append({"texto": rc, "chave": tipo_cd})

                        res_vc = vitoria_casa.verificar_vitoria_casa(s_inicial)
                        for rv in res_vc:
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # ----------------------------------------------------------
                        # FASE 2: RASPAGEM DE ESTATÍSTICAS COLETIVAS (ESCANTEIOS)
                        # ----------------------------------------------------------
                        print(f"      📊 [FASE 2] Buscando Estatísticas Coletivas (Escanteios)...")
                        s = pegar_estatisticas_coletivas(driver, s_inicial)

                        res_escanteios = analisar_dados_escanteios(
                            s.get("cantos_mandante_h2h", []), 
                            s.get("cantos_visitante_h2h", []), 
                            nome_comp, 
                            3
                        )
                        if res_escanteios and res_escanteios.get("aprovado"):
                            mercado_cantos_formatado = res_escanteios.get("mercado")
                            if mercado_cantos_formatado:
                                chave_cantos = "CANTOS_UNDER" if "Menos" in mercado_cantos_formatado else "CANTOS_OVER"
                                mercados_para_processar.append({"texto": mercado_cantos_formatado, "chave": chave_cantos})
                                print(f"         ✅ Mercado de Cantos Qualificado: {mercado_cantos_formatado}")

                        # ----------------------------------------------------------
                        # FASE 3: RASPAGEM DE SCOUTS (JOGADORES) - SÓ SE LIGA ELITE
                        # ----------------------------------------------------------
                        if nome_comp in LIGAS_ELITE_JOGADORES:
                            print(f"      🎯 [FASE 3] Buscando Scouts Avançados (Chutes/Faltas)...")
                            s = pegar_scouts_avancados(driver, s, t1, t2)
                            
                            elenco_casa_disponivel = s.get("elenco_mandante") or s.get("jogadores_mandante")
                            elenco_fora_disponivel = s.get("elenco_visitante") or s.get("jogadores_visitante")
                            
                            nome_time_casa = t1 if t1 else "MANDANTE"
                            nome_time_fora = t2 if t2 else "VISITANTE"

                            # Jogadores (Chutes no Alvo) 
                            res_jogadores = jogadores.verificar_destaques_jogadores(
                                s.get("historico_chutes", {}), 3, nome_comp,
                                elenco_casa=elenco_casa_disponivel, elenco_fora=elenco_fora_disponivel,
                                nome_casa=nome_time_casa, nome_fora=nome_time_fora
                            )
                            for rj in res_jogadores:
                                mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                            # Jogadores (Faltas Sofridas) 
                            res_faltas = jogadores.verificar_destaques_faltas(
                                s.get("historico_faltas", {}), 3, nome_comp,
                                elenco_casa=elenco_casa_disponivel, elenco_fora=elenco_fora_disponivel,
                                nome_casa=nome_time_casa, nome_fora=nome_time_fora
                            )
                            for rf in res_faltas:
                                mercados_para_processar.append({"texto": rf['texto'], "chave": rf['chave']})
                        else:
                            print(f"      ⏩ [OTIMIZAÇÃO] Pulando scouts avançados para {nome_comp} (Não é liga Elite).")

                        # TRAVA ANTI-DUPLICADOS
                        mercados_unicos = []
                        textos_vistos = set()
                        for item in mercados_para_processar:
                            if item["texto"] not in textos_vistos:
                                mercados_unicos.append(item)
                                textos_vistos.add(item["texto"])
                        mercados_para_processar = mercados_unicos

                        # Log de auditoria para acompanhar no GitHub Actions
                        print(f"      🔍 Mercados pré-aprovados antes das odds: {[m['texto'] for m in mercados_para_processar]}")

                        # --- VALIDAÇÃO DE ODDS ---
                        if mercados_para_processar:
                            try:
                                v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            except Exception as e_odds:
                                if "invalid session id" in str(e_odds).lower() or "session" in str(e_odds).lower():
                                    print("      ⚠️ [RECUPERAÇÃO] Driver caiu antes das odds! Reiniciando navegador...")
                                    try: driver.quit()
                                    except: pass
                                    driver = configurar_driver()
                                    try:
                                        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo")
                                        time.sleep(3)
                                        v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                                    except:
                                        v_odds = {}
                                else:
                                    v_odds = {}
                            
                            for item in mercados_para_processar:
                                m_texto, m_chave = item["texto"], item["chave"]
                                
                                # Mapeia as chaves virtuais e fixas de análise para evitar quebras por N/A
                                if m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CANTOS_OVER", "CANTOS_UNDER"]:
                                    valor_odd_str = "1.50" 
                                else:
                                    valor_odd_str = v_odds.get(m_chave, "N/A")

                                try:
                                    odd_float = float(str(valor_odd_str).replace(',', '.'))
                                except (ValueError, TypeError, AttributeError):
                                    print(f"      ⚠️ Descartado (Odd inválida): {m_texto} | Valor: {valor_odd_str}")
                                    continue 

                                if "M45" in m_chave and odd_float >= 4.0: continue 
                                
                                texto_limpo = m_texto.strip()
                                if m_chave == "CHUTES_ALVO" and (texto_limpo == "0.0" or texto_limpo.startswith("0.0")): continue

                                if odd_float >= 1.25:
                                    lista_para_filtros.append({
                                        "horario": h_br, "time_casa": t1, "time_fora": t2,
                                        "mercado": m_texto, "odd": valor_odd_str if m_chave not in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CANTOS_OVER", "CANTOS_UNDER"] else "Análise", "liga": nome_comp,
                                        "link_betano": s.get("link_betano")
                                    })
                                    jogos_para_pendentes.append({
                                        "time_casa": t1, "time_fora": t2, "mercado": m_texto,
                                        "mercado_ranking": m_texto.upper(), "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                    })
                                    total_mercados += 1
                                    
                except Exception as e:
                    if "invalid session id" in str(e).lower() or "session" in str(e).lower():
                        print("⚠️ [CRÍTICO] Sessão inválida detectada no loop interno. Reiniciando driver...")
                        try: driver.quit()
                        except: pass
                        driver = configurar_driver()
                    else:
                        print(f"⚠️ Erro ao processar partida no loop interno: {e}")
                    continue

        # --- PROCESSAMENTO E ENVIO FINAL ---
        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            meu_chat_id = os.getenv('CHAT_ID')
            if meu_chat_id:
                cabecalho = "🚧 *LISTA DE TESTE MERCADOS DO DIA*\n\n"
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
                chave = f"{j['time_casa']}x{j['time_fora']}"
                cache_dados[chave] = {
                    "link": j.get("link_betano"),
                    "liga": j.get("liga"),
                    "horario": j.get("horario"),
                    "odd": j.get("odd")
                }
    
            print("📢 Pulando envio do Elite conforme solicitado.")
    
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
                json.dump([{"horario": j.get("horario"), "liga": j.get("liga"), "time_casa": j.get("time_casa"), "time_fora": j.get("time_fora"), "mercado": j.get("mercado"), "odd": j.get("odd"), "link_betano": j.get("link_betano")} for j in lista_para_filtros], f, indent=4, ensure_ascii=False)
        else:
            print("⚠️ Nenhuma partida qualificada entrou na 'lista_para_filtros' após varrer os elementos.")

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
                    
