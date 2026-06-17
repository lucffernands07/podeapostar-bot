import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importação dos seus módulos (Incluindo o novo mercados/jogadores.py)
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores
import odds  
import bingo357  
import links
from telegram import menus


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
    options.add_argument("--headless=new") # Versão mais rápida do headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") # Desliga processamento gráfico
    options.add_argument("--blink-settings=imagesEnabled=false") # Não carrega imagens (ganha muita velocidade)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    # Navegação inicial - Abre a aba do jogo
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_45_under": 0, "fora_btts": 0, 
        "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", 
        "h2h_geral_res_1": "", "h2h_geral_res_2": "", "h2h_geral_res_3": "", "h2h_geral_res_4": "", "h2h_geral_res_5": "",
        "t1_placar_1": None, "t2_placar_1": None,     
        "h2h_placar_1": None, "h2h_placar_2": None,   
        "pular_gols": False,
        # 📦 NOVAS CHAVES: Guardam os históricos brutos mapeados nas sub-abas
        "historico_chutes": {},
        "historico_faltas": {}
    }
    
    try:
        wait = WebDriverWait(driver, 15)
        # 1. Vai para a aba H2H onde estão os seus links
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t1_para_jogadores = []
        
        for idx, secao in enumerate(secoes[:3]): 
            if idx == 2: 
                try:
                    seletor_btn = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao.find_element(By.CSS_SELECTOR, seletor_btn)
                    driver.execute_script("arguments[0].click();", botao_mais)
                    WebDriverWait(secao, 6).until(lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6)
                except: pass 

            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            if idx == 0:
                linhas_t1_para_jogadores = linhas

            for i, linha in enumerate(linhas):

                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                    
                    if idx == 0 and i == 0: stats["t1_placar_1"] = res_texto
                    if idx == 1 and i == 0: stats["t2_placar_1"] = res_texto
                    if idx == 2:
                        if i == 0: stats["h2h_placar_1"] = res_texto
                        if i == 1: stats["h2h_placar_2"] = res_texto

                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    total = g1 + g2

                    if idx < 2: 
                        prefixo = "casa" if idx == 0 else "fora"
                        t_ref = t1 if idx == 0 else t2
                        if i == 0: stats[f"ultimo_gols_{prefixo}"] = total
                        if total > 1.5: stats[f"{prefixo}_15"] += 1
                        if total > 2.5: stats[f"{prefixo}_25"] += 1
                        if total <= 4: stats[f"{prefixo}_45_under"] += 1 
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1
                        
                        res_atual = "E"
                        if (t_ref.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t_ref.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_atual = "V"
                            stats[f"{prefixo}_vitorias_recente"] += 1
                        elif (t_ref.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t_ref.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_atual = "D"
                        
                        if i == 0: stats[f"t{idx+1}_resultado_1"] = res_atual
                 
                    elif idx == 2: 
                        if i < 5:
                            res_geral = "EMPATE"
                            if g1 > g2:
                                if t1.lower() in n_casa_h2h.lower(): res_geral = "CASA"
                                elif t2.lower() in n_casa_h2h.lower(): res_geral = "FORA"
                            elif g1 < g2:
                                if t1.lower() in n_fora_h2h.lower(): res_geral = "CASA"
                                elif t2.lower() in n_fora_h2h.lower(): res_geral = "FORA"
                            
                            stats[f"h2h_geral_res_{i+1}"] = res_geral

                        if t1.lower() in n_fora_h2h.lower():
                            continue 

                        stats["h2h_jogos"] += 1
                        res_h2h = "E"
                        if g1 > g2:
                            res_h2h = "V"
                            stats["h2h_vitorias_t1"] += 1
                        elif g1 < g2:
                            res_h2h = "D"
                            stats["h2h_vitorias_t2"] += 1
                        
                        if stats["h2h_res_1"] == "":
                            stats["h2h_res_1"] = res_h2h
                        elif stats["h2h_res_2"] == "":
                            stats["h2h_res_2"] = res_h2h

                        if g1 == g2: stats["h2h_empates"] += 1

                except: continue

        # -----------------------------------------------------------------
        # 🚀 EXTRAÇÃO DOS DETALHES DE JOGADORES (APENAS NAS LINHAS VALIDADAS)
        # -----------------------------------------------------------------
        if len(linhas_t1_para_jogadores) >= 3:
            url_inicial_confronto = driver.current_url
            
            for jogo_index in range(3):
                if jogo_index > 0:
                    driver.get(url_inicial_confronto)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    secoes_atualizadas = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
                    linhas_t1_para_jogadores = secoes_atualizadas[0].find_elements(By.CSS_SELECTOR, ".h2h__row")

                elemento_alvo = linhas_t1_para_jogadores[jogo_index]
                url_anterior = driver.current_url
                
                driver.execute_script("arguments[0].click();", elemento_alvo)
                try: WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                except: pass
                    
                time.sleep(2.5)
                url_jogo_completa = driver.current_url.split("?")[0].strip("/")

                # --- 🎯 Sub-Aba: Finalizações ---
                driver.get(f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/")
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fp-playerName_E6lgN")))
                    cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], th")
                    indice_chutes = 10
                    for idx_c, th in enumerate(cabecalhos):
                        texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                        alias = str(th.get_attribute("data-analytics-alias")).upper()
                        if "ALVO" in texto_th or alias == "SHOTS_ON_TARGET":
                            indice_chutes = idx_c
                            break
                    
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, ".wcl-table__row_") or driver.find_elements(By.TAG_NAME, "tr")
                    for linha in linhas_dados:
                        try:
                            nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                            if not nome_jogador or nome_jogador == "TODOS": continue
                            celulas = linha.find_elements(By.CSS_SELECTOR, ".wcl-table__bodyCell_, td")
                            if len(celulas) > indice_chutes:
                                valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas[indice_chutes]).strip()
                                chutes = 0 if valor_bruto in ["-", ""] else int(valor_bruto)
                                if nome_jogador not in stats["historico_chutes"]: stats["historico_chutes"][nome_jogador] = []
                                while len(stats["historico_chutes"][nome_jogador]) < jogo_index: stats["historico_chutes"][nome_jogador].append(0)
                                stats["historico_chutes"][nome_jogador].append(chutes)
                        except: continue
                except: pass

                # --- 🤕 Sub-Aba: Ataque (Faltas Sofridas) ---
                driver.get(f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/")
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fp-playerName_E6lgN")))
                    cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], th")
                    indice_base = 13
                    for idx_c, th in enumerate(cabecalhos):
                        texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                        alias = str(th.get_attribute("data-analytics-alias")).upper()
                        if alias == "FOULS_SUFFERED" or "SOFRIDAS" in texto_th:
                            indice_base = idx_c
                            break
                    
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, ".wcl-table__row_") or driver.find_elements(By.TAG_NAME, "tr")
                    indice_real_faltas = -1
                    for test_idx in range(indice_base, -1, -1):
                        encontrou_valor = False
                        for linha in linhas_dados:
                            try:
                                celulas = linha.find_elements(By.CSS_SELECTOR, ".wcl-table__bodyCell_, td")
                                if len(celulas) > test_idx:
                                    v = driver.execute_script("return arguments[0].textContent;", celulas[test_idx]).strip()
                                    if v.isdigit() and int(v) >= 1:
                                        encontrou_valor = True
                                        break
                            except: continue
                        if encontrou_valor:
                            indice_real_faltas = test_idx
                            break
                    if indice_real_faltas == -1: indice_real_faltas = indice_base - 1

                    for linha in linhas_dados:
                        try:
                            nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                            if not nome_jogador or nome_jogador == "TODOS": continue
                            celulas = linha.find_elements(By.CSS_SELECTOR, ".wcl-table__bodyCell_, td")
                            if len(celulas) > indice_real_faltas:
                                valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas[indice_real_faltas]).strip()
                                faltas = 0 if valor_bruto in ["-", ""] or "%" in valor_bruto or "/" in valor_bruto else int(valor_bruto)
                                if nome_jogador not in stats["historico_faltas"]: stats["historico_faltas"][nome_jogador] = []
                                while len(stats["historico_faltas"][nome_jogador]) < jogo_index: stats["historico_faltas"][nome_jogador].append(0)
                                stats["historico_faltas"][nome_jogador].append(faltas)
                        except: continue
                except: pass
        # -----------------------------------------------------------------

        print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
        stats["link_betano"] = links.extrair_url_betano(driver)

    except Exception as e:
        print(f"      ⚠️ Erro H2H {t1}x{t2}: {e}")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats


def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    jogos_para_pendentes = [] 
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: break 
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
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_obj = datetime.strptime(tempo_raw.split()[-1], "%H:%M")
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
                        s = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
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
def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    jogos_para_pendentes = [] 
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: break 
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
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_obj = datetime.strptime(tempo_raw.split()[-1], "%H:%M")
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
                        s = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
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

                        # 🚀 5. PROCESSAMENTO DO NOVO MERCADO DE JOGADORES (MÉDIAS)
                        res_jogadores = jogadores.verificar_destaques_jogadores(s.get("historico_chutes", {}), s.get("historico_faltas", {}))
                        for rj in res_jogadores:
                            mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})

                        # --- VALIDAÇÃO DE ODDS E FILTRAGEM COM BYPASS PARA JOGADORES ---
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            
                            for item in mercados_para_processar:
                                m_texto = item["texto"]
                                m_chave = item["chave"]
                                
                                # Injeta odd fixa se for mercado de jogador para o validador aprovar
                                if m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS"]:
                                    valor_odd_str = "1.50"
                                else:
                                    valor_odd_str = v_odds.get(m_chave, "N/A")

                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    
                                    if "M45" in m_chave and odd_float >= 4.0:
                                        continue 

                                    # 🚀 RÉGUA SUBIU: Mínimo 1.40
                                    if odd_float >= 1.40:
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m_texto, "odd": valor_odd_str if m_chave not in ["CHUTES_ALVO", "FALTAS_SOFRIDAS"] else "Análise", "liga": nome_comp,
                                            "link_betano": s.get("link_betano")
                                        })
                                        
                                        jogos_para_pendentes.append({
                                            "time_casa": t1,
                                            "time_fora": t2,
                                            "mercado": m_texto,
                                            "mercado_ranking": m_texto.upper(),
                                            "link_h2h": f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                                        })
                                                
                                        total_mercados += 1
                                except: continue
                except: continue

        # --- PROCESSAMENTO E ENVIO FINAL ---
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

            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            cache_dados = {}
            for j in lista_para_filtros:
                chave = f"{j['time_casa']}x{j['time_fora']}"
                cache_dados[chave] = {
                    "link": j.get("link_betano"),
                    "liga": j.get("liga"),
                    "horario": j.get("horario"),
                    "odd": j.get("odd")
                }
            texto_bingos_final = bingo357.formatar_para_telegram(novos_bilhetes, cache_dados)

            canal_id = os.getenv('CHANNEL_ID')
            if texto_bingos_final and canal_id:
                msg_bingo_formatada = "💰 *SUGESTÕES DE INVESTIMENTO*\n\n" + texto_bingos_final
                menus.enviar_menu_bingo(canal_id, msg_bingo_formatada)
                print("📢 Bingos enviados com botões para o Canal.")

            # --- TRATAMENTO DOS ARQUIVOS DE RANKING E BANCO LOCAL ---
            import json
            os.makedirs("ranking", exist_ok=True)
            caminho_p = "ranking/pendentes.json"
            data_hoje = hoje_ref.strftime("%Y-%m-%d")
            
            pode_gravar = True 

            if os.path.exists(caminho_p):
                try:
                    with open(caminho_p, 'r', encoding='utf-8') as f:
                        conteudo = f.read().strip()
                        if conteudo:
                            dados_existentes = json.loads(conteudo)
                            if dados_existentes.get("data_geracao") == data_hoje:
                                if len(dados_existentes.get("jogos", [])) > 0:
                                    pode_gravar = False
                except (json.JSONDecodeError, Exception) as e:
                    print(f"⚠️ Arquivo de ranking corrompido ou ilegível, resetando: {e}")
                    pode_gravar = True

            if pode_gravar and jogos_para_pendentes: 
                dados_final = {
                    "data_geracao": data_hoje,
                    "jogos": jogos_para_pendentes 
                }
                with open(caminho_p, "w", encoding="utf-8") as f:
                    json.dump(dados_final, f, indent=4, ensure_ascii=False)
                print(f"✅ Ranking: Primeira execução do dia salva ({len(jogos_para_pendentes)} jogos).")
            elif not pode_gravar:
                print(f"🚫 BLOQUEIO: O Ranking de hoje ({data_hoje}) já foi consolidado na 1ª execução.")

            os.makedirs("telegram", exist_ok=True)
            caminho_banco = f"telegram/jogos_{data_hoje}.json"

            dados_para_o_bot = []
            for j in lista_para_filtros:
                dados_para_o_bot.append({
                    "horario": j.get("horario"),
                    "liga": j.get("liga"),
                    "time_casa": j.get("time_casa"),
                    "time_fora": j.get("time_fora"),
                    "mercado": j.get("mercado"),
                    "odd": j.get("odd"),
                    "link_betano": j.get("link_betano") 
                })

            with open(caminho_banco, "w", encoding="utf-8") as f:
                json.dump(dados_para_o_bot, f, indent=4, ensure_ascii=False)

            print(f"📂 Banco de dados do dia salvo para o Bot: {caminho_banco}")
            print("✅ Processamento concluído com sucesso.")

    except Exception as e:
        print(f"❌ Erro Crítico no Main: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
