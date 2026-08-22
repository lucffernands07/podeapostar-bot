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

# Módulos de Mercados Ativos (Sem trava de liga)
from ligas import COMPETICOES 
from mercados import gols, ambos_marcam, chance_dupla, vitorias, chutes_totais, escanteios, cartoes
import odds, bingo357
from telegram import menus

# Funções de Raspagem (Adaptadas para Superscore)
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
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
     
    jogos_brutos_coletados = []  # Armazena os dados coletados antes de buscar odds
    jogos_para_pendentes = []  
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: 
                break 
            print(f"\n--- Analisando: {nome_comp} ---")
             
            url_calendario = url.rstrip("/").replace("/jogos", "").replace("/resultados", "") + "/calendario/"
             
            try:
                driver.get(url_calendario)
                time.sleep(3)  
                 
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
                    driver.get(url_calendario)
                    time.sleep(3)
                    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                else:
                    print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                    continue
             
            total_elementos = len(elementos)
             
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
                        print(f"     ⏩ Pulado: Não encontrou nenhum elemento de tempo.")
                        continue

                    if "Preview" in tempo_raw:
                        tempo_raw = tempo_raw.replace("Preview", "").strip()

                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                        print(f"     ⏩ Pulado: Status ao vivo/encerrado detectado ({tempo_raw})")
                        continue

                    if not tempo_raw:
                        continue

                    amanha_ref = hoje_ref + timedelta(days=1)
                    hoje_no_site = hoje_ref.strftime("%d.%m.")
                    amanha_no_site = amanha_ref.strftime("%d.%m.")

                    eh_hoje = hoje_no_site in tempo_raw
                    eh_madrugada_seguinte = amanha_no_site in tempo_raw and any(f"{h:02d}:" in tempo_raw for h in range(3))

                    if not (eh_hoje or eh_madrugada_seguinte):
                        continue

                    partes_tempo = tempo_raw.split()
                    if not partes_tempo: 
                        continue

                    horario_str = partes_tempo[-1]
                    if ":" not in horario_str: 
                        continue

                    try:
                        h_obj = datetime.strptime(horario_str, "%H:%M")
                        hora_dt = datetime.now().replace(hour=h_obj.hour, minute=h_obj.minute, second=0, microsecond=0)
                        hora_br_dt = hora_dt - timedelta(hours=3)
                        h_br = hora_br_dt.strftime("%H:%M")
                        print(f"     ⏰ Data/Hora OK | UTC: {horario_str} | Horário BR: {h_br}")
                    except Exception as e:
                        print(f"     ⚠️ Erro ao processar horário '{tempo_raw}': {e}")
                        continue

                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    if len(times) < 2:
                        print(f"     ⚠️ Falha: Não conseguiu ler os nomes dos dois times no elemento.")
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
                        print(f"     ⚠️ Falha: ID do jogo inválido ou não encontrado.")
                        continue

                    print(f"     ✅ JOGO QUALIFICADO: {t1} x {t2} (ID: {id_jogo}) - Raspando estatísticas e H2H...")

                    # ----------------------------------------------------------
                    # PASSO 2 & 4: RASPAGEM PURA NO SUPERSCORE (Estatísticas + H2H 2025/2026)
                    # ----------------------------------------------------------
                    url_jogo_base = f"https://www.flashscore.com.br/jogo/{id_jogo}"
                    dados_jogo = pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2)
                    
                    if not isinstance(dados_jogo, dict):
                        dados_jogo = {}

                    dados_jogo["url_h2h_base"] = f"https://www.superscore.com/jogo/{id_jogo}/#/resumo-de-jogo"
                    dados_jogo["liga"] = nome_comp

                    # Raspagem Estatística Coletiva
                    try:
                        dados_coletivos = pegar_estatisticas_coletivas(driver, dados_jogo)
                        if dados_coletivos and isinstance(dados_coletivos, dict):
                            dados_jogo.update(dados_coletivos)
                    except Exception as e_f2:
                        print(f"     ⚠️ Erro nas Estatísticas Coletivas: {e_f2}")

                    mercados_jogo_encontrados = []

                    # --- AVALIAÇÃO DE MERCADOS (Passo 5) ---
                    # 1° GOLS
                    try:
                        res_gols = gols.verificar_gols(dados_jogo)
                        for rg in res_gols:
                            if isinstance(rg, dict):
                                mercados_jogo_encontrados.append({"texto": rg['mercado'], "chave": rg['tipo'], "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Gols: {e}")

                    # 2° CHANCE DUPLA
                    try:
                        res_cd = chance_dupla.verificar_chance_dupla(dados_jogo)
                        for rc in res_cd:
                            texto_cd = rc if isinstance(rc, str) else rc.get("mercado", "")
                            tipo_cd = "1X" if "1X" in texto_cd else "X2"
                            mercados_jogo_encontrados.append({"texto": texto_cd, "chave": tipo_cd, "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Chance Dupla: {e}")

                    # 3° VITÓRIAS
                    try:
                        res_vitorias = vitorias.verificar_vitorias(dados_jogo)
                        for rv in res_vitorias:
                            texto_vic = rv if isinstance(rv, str) else rv.get("mercado", "")
                            chave_vic = "VITORIA_FORA" if "Fora" in texto_vic else "VITORIA_CASA"
                            mercados_jogo_encontrados.append({"texto": texto_vic, "chave": chave_vic, "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Vitórias: {e}")

                    # 4° AMBOS MARCAM
                    try:
                        lista_gols_segura = res_gols if 'res_gols' in locals() and isinstance(res_gols, list) else []
                        res_btts = ambos_marcam.verificar_btts(dados_jogo, mercados_gols_aprovados=lista_gols_segura, odds_jogo={})
                        for rb in res_btts:
                            if isinstance(rb, dict):
                                mercados_jogo_encontrados.append({"texto": rb.get("mercado", ""), "chave": rb.get("tipo", "BTTS"), "odd": "Análise"})
                            elif isinstance(rb, str):
                                chave_btts = "BTTS_NAO" if "Não" in rb or "Nao" in rb else "BTTS"
                                mercados_jogo_encontrados.append({"texto": rb, "chave": chave_btts, "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em BTTS: {e}")

                    # 5° CHUTES
                    try:
                        res_chutes = chutes_totais.verificar_chutes_totais(dados_jogo)
                        for rc in res_chutes:
                            if rc.get("mercado"):
                                mercados_jogo_encontrados.append({"texto": rc["mercado"], "chave": rc["tipo"], "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Chutes: {e}")

                    # 6° ESCANTEIOS
                    try:
                        res_cantos = escanteios.analisar_dados_escanteios(
                            dados_jogo.get("cantos_mandante_h2h", []), 
                            dados_jogo.get("cantos_visitante_h2h", []), 
                            nome_liga=nome_comp
                        )
                        if res_cantos.get("aprovado"):
                            mercados_jogo_encontrados.append({"texto": res_cantos["mercado"], "chave": "ESCANTEIOS_JOGO", "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Escanteios: {e}")

                    # 7° CARTÕES
                    try:
                        res_cartoes = cartoes.analisar_dados_cartoes(
                            dados_jogo.get("cartoes_mandante_h2h", []), 
                            dados_jogo.get("cartoes_visitante_h2h", []), 
                            nome_liga=nome_comp, 
                            dados_incompletos=dados_jogo.get("dados_incompletos_cartoes", False)
                        )
                        if res_cartoes.get("aprovado"):
                            mercados_jogo_encontrados.append({"texto": res_cartoes["mercado"], "chave": "CARTOES_JOGO", "odd": "Análise"})
                    except Exception as e:
                        print(f"     ⚠️ Erro em Cartões: {e}")

                    # Se o jogo teve mercados aprovados, guarda para a fase de enriquecimento de odds
                    if mercados_jogo_encontrados:
                        print(f"     ✅ {len(mercados_jogo_encontrados)} mercado(s) aprovado(s) para {t1} x {t2}!")
                        jogos_brutos_coletados.append({
                            "horario": h_br,
                            "time_casa": t1,
                            "time_fora": t2,
                            "liga": nome_comp,
                            "id_jogo": id_jogo,
                            "link_h2h": dados_jogo["url_h2h_base"],
                            "mercados": mercados_jogo_encontrados
                        })
                    else:
                        print(f"     ⏩ Nenhum mercado atingiu os critérios para {t1} x {t2}.")

                    try:
                        driver.get(url_calendario)
                        time.sleep(2.0)
                    except Exception as e_volta:
                        print(f"⚠️ Erro ao recarregar a liga: {e_volta}")

                except Exception as e_jogo:
                    print(f"     ⚠️ Erro ao processar o jogo índice {idx}: {e_jogo}")
                    continue

        # ----------------------------------------------------------
        # PASSO 6: ENRIQUECIMENTO DE ODDS E LINKS (Apenas para jogos aprovados)
        # ----------------------------------------------------------
        lista_para_filtros = []
        ids_jogos_salvos_pendentes = set()

        if jogos_brutos_coletados:
            print(f"\n🔍 Iniciando captura de Odds e Links da Betano para {len(jogos_brutos_coletados)} jogos qualificados...")
            for item_jogo in jogos_brutos_coletados:
                t1 = item_jogo["time_casa"]
                t2 = item_jogo["time_fora"]
                id_jogo = item_jogo["id_jogo"]

                v_odds = {}
                link_betano_capturado = None
                try:
                    print(f"     🔍 Buscando odds e link Betano para: {t1} x {t2}...")
                    v_odds = odds.capturar_todas_as_odds(driver, t1, t2)
                    # O odds.py ou a função de link já lida com o link do banner se integrado, 
                    # mantendo a compatibilidade com o retorno do odds.
                except Exception as e_odds:
                    print(f"     ⚠️ Erro ao capturar odds para {t1} x {t2}: {e_odds}")
                    if "invalid session id" in str(e_odds).lower() or "session" in str(e_odds).lower():
                        try: driver.quit()
                        except: pass
                        driver = configurar_driver()

                if id_jogo not in ids_jogos_salvos_pendentes:
                    jogos_para_pendentes.append({
                        "time_casa": t1, 
                        "time_fora": t2, 
                        "mercado": "MÚLTIPLOS",
                        "mercado_ranking": "LISTÃO GERAL", 
                        "link_h2h": item_jogo["link_h2h"]
                    })
                    ids_jogos_salvos_pendentes.add(id_jogo)

                for m in item_jogo["mercados"]:
                    m_chave = m["chave"]
                    m_texto = m["texto"]
                    
                    # Tenta resgatar a odd real se houver correspondência na chave, senão mantém "Análise" ou o valor lido
                    valor_odd = v_odds.get(m_chave, "Análise")
                    if valor_odd != "Análise" and valor_odd != "N/A":
                        try:
                            odd_float = float(str(valor_odd).replace(',', '.'))
                            if odd_float >= 1.10:
                                valor_odd = str(odd_float)
                            else:
                                continue # Descarta se odd for menor que 1.10 quando existente
                        except:
                            pass

                    lista_para_filtros.append({
                        "horario": item_jogo["horario"],
                        "time_casa": t1,
                        "time_fora": t2,
                        "mercado": m_texto,
                        "odd": valor_odd,
                        "liga": item_jogo["liga"],
                        "link_betano": v_odds.get("link_betano"),
                        "link_h2h": item_jogo["link_h2h"],
                        "odds_todas": v_odds
                    })
                    total_mercados += 1

        # ----------------------------------------------------------
        # PASSO 7: PROCESSAMENTO E ENVIO FINAL (Telegram e Arquivos)
        # ----------------------------------------------------------
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
             
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros, qtd_alvo=None)
            textos_bingos_lista = bingo357.formatar_para_telegram(novos_bilhetes, cache_dados)
    
            if textos_bingos_lista and canal_id:
                for idx, texto_part in enumerate(textos_bingos_lista):
                    try:
                        msg_bingo_formatada = texto_part
                        if idx == 0:
                            msg_bingo_formatada = "💰 *LISTA COMPLETA AGRUPADA*\n\n" + msg_bingo_formatada
                             
                        menus.enviar_menu_bingo(canal_id, msg_bingo_formatada)
                        print(f"📢 Parte {idx+1}/{len(textos_bingos_lista)} enviada para o Canal.")
                        time.sleep(1.5) 
                    except Exception as e:
                        print(f"⚠️ Erro ao enviar a parte {idx+1} para o canal: {e}")

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
