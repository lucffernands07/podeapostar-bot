import os
import requests
import urllib.parse
import time
import re
import pytz
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def get_sofa_h2h_corners(driver, t1_name, t2_name):
    """ MOTOR COM ORDEM DE MANDO: Respeita Casa x Fora para garantir o ID correto """
    url_real_com_id = "https://www.sofascore.com/"
    wait = WebDriverWait(driver, 25)
    try:
        driver.get("https://www.sofascore.com/pt/")
        
        try:
            cookies_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Agree')]")
            if cookies_btn: cookies_btn[0].click()
        except: pass

        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(10)
        
        resultado_xpath = "//a[contains(@href, '/football/match/')]"
        try:
            resultados = driver.find_elements(By.XPATH, resultado_xpath)
            if not resultados:
                search_input.clear()
                search_input.send_keys(t1_name)
                time.sleep(7)
                resultados = driver.find_elements(By.XPATH, resultado_xpath)

            resultado_link = resultados[0]
            url_real_com_id = resultado_link.get_attribute("href")
            driver.get(url_real_com_id)
        except Exception as e:
            print(f"Não localizou link de partida para {t1_name}: {e}")
            return None, 0, url_real_com_id
        
        url_h2h = url_real_com_id.split('#')[0] + "#tab:matches"
        driver.get(url_h2h)
        time.sleep(15)
        
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(5)
        
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        percs_menos = []
        
        matches = re.finditer(r"Menos.*?10\.5", texto_bruto, re.IGNORECASE | re.DOTALL)
        for m in matches:
            trecho = texto_bruto[m.end() : m.end() + 65]
            busca_f = re.search(r"(\d+)/(\d+)", trecho)
            if busca_f:
                n, d = int(busca_f.group(1)), int(busca_f.group(2))
                if d >= 5:
                    percs_menos.append((n / d) * 100)

        if percs_menos:
            percs_unicos = sorted(list(set(percs_menos)), reverse=True)
            valor_calculado = percs_unicos[0]
            if len(percs_unicos) >= 2:
                valor_calculado = (percs_unicos[0] + percs_unicos[1]) / 2
            
            if valor_calculado >= 80:
                return "Menos 10.5 Escanteios", valor_calculado, url_real_com_id
    
    except Exception as e:
        print(f"Erro Sofa {t1_name} x {t2_name}: {e}")
    return None, 0, url_real_com_id

def get_h2h_dupla_chance(t1_id, t2_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0
        t1_wd, t2_wd = 0, 0
        for f in fixtures:
            gh, ga = f['goals']['home'], f['goals']['away']
            if (f['teams']['home']['id'] == t1_id and gh >= ga) or (f['teams']['away']['id'] == t1_id and ga >= gh): t1_wd += 1
            if (f['teams']['home']['id'] == t2_id and gh >= ga) or (f['teams']['away']['id'] == t2_id and ga >= gh): t2_wd += 1
        return (t1_wd / len(fixtures)) * 100, (t2_wd / len(fixtures)) * 100
    except: return 0, 0

def get_individual_stats(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        o15 = 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total >= 2: o15 += 1
        return (o15 * 10)
    except: return 0

def executar():
    browser = configurar_browser()
    
    # --- AJUSTE FUSO HORÁRIO ---
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    ligas = {
        2: "Champions League", 39: "Premier League", 140: "LALIGA", 135: "Serie A", 
        78: "Bundesliga", 61: "Ligue 1", 94: "Português", 71: "Brasileirão A", 
        88: "Holandês", 144: "Belga", 203: "Süper Lig", 172: "Bulgária", 
        265: "Chile", 239: "Colômbia", 233: "Egito", 141: "LaLiga 2", 
        72: "Brasileirão B", 13: "Libertadores", 11: "Sudamericana"
    }
    
    pool_entradas = []

    for l_id, l_nome in ligas.items():
        fixtures_hoje = []
        for ano in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                if res.get('response'):
                    fixtures_hoje = res['response']
                    break
            except: continue

        for m in fixtures_hoje:
            hora_utc = datetime.fromisoformat(m['fixture']['date'].replace('Z', '+00:00'))
            hora_br = hora_utc.astimezone(fuso_br).strftime("%H:%M")

            t1, t2 = m['teams']['home'], m['teams']['away']
            tipo_canto, perc_canto, url_real_sofa = get_sofa_h2h_corners(browser, t1['name'], t2['name'])

            g_info = {
                "id": m['fixture']['id'], 
                "info": f"*{t1['name']} x {t2['name']}*", 
                "hora": hora_br, 
                "liga": l_nome, 
                "sofa_link": url_real_sofa 
            }

            if tipo_canto and perc_canto >= 80:
                pool_entradas.append({"perc": perc_canto, "mkt": tipo_canto, "tipo": "canto", **g_info})

            h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
            if h2h_t1 >= 80: 
                pool_entradas.append({"perc": h2h_t1, "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
            if h2h_t2 >= 90: 
                pool_entradas.append({"perc": h2h_t2, "mkt": f"{t2['name']} ou Empate", "tipo": "2x", **g_info})

            h_o15 = get_individual_stats(t1['id'])
            a_o15 = get_individual_stats(t2['id'])
            m_o15 = (h_o15 + a_o15)/2
            if m_o15 >= 70: 
                pool_entradas.append({"perc": m_o15, "mkt": "+1.5 Gols", "tipo": "1.5", **g_info})
                
    # --- FECHA O NAVEGADOR APÓS TERMINAR TODAS AS LIGAS ---
    browser.quit()
    
    # RANKING GERAL POR %
    pool_entradas.sort(key=lambda x: x['perc'], reverse=True)
    
    jogos_selecionados = {}
    total_mercados = 0  # <--- Nova variável para controlar o limite de 13

    for e in pool_entradas:
        mid = e['id']
        
        # Se já atingiu 13 mercados no total, para de processar a lista
        if total_mercados >= 13:
            break
            
        # Mantém sua lógica de no máximo 10 jogos diferentes
        if mid not in jogos_selecionados and len(jogos_selecionados) >= 10: 
            continue
            
        if mid not in jogos_selecionados:
            jogos_selecionados[mid] = {
                "info": e['info'], 
                "hora": e['hora'], 
                "liga": e['liga'], 
                "link": e['sofa_link'], 
                "mkts": []
            }
        
        # Adiciona o mercado se o jogo tiver menos de 3 (sua regra)
        # E se ainda houver espaço no limite global de 13
        if len(jogos_selecionados[mid]["mkts"]) < 3 and total_mercados < 13:
            jogos_selecionados[mid]["mkts"].append(e)
            total_mercados += 1  # <--- Soma +1 ao contador global

    # Remove jogos que possam ter ficado vazios por causa do limite
    jogos_selecionados = {k: v for k, v in jogos_selecionados.items() if v["mkts"]}

    if not jogos_selecionados: return
    lista_final = sorted(jogos_selecionados.values(), key=lambda x: x['liga'])


    msg = "🎯 *BILHETE DO DIA (SISTEMA H2H)*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, j in enumerate(lista_final, 1):
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        j['mkts'].sort(key=lambda x: x['perc'], reverse=True)
        for mkt in j['mkts']:
            if mkt['tipo'] == 'canto': label = f"🚩 {mkt['mkt']} {mkt['perc']:.0f}%"
            elif mkt['tipo'] in ['1x', '2x']: label = f"🛡️ {mkt['mkt']} ({mkt['perc']:.0f}%)"
            else: label = f"⚽ {mkt['mkt']} ({mkt['perc']:.0f}%)"
            msg += f"🔶 {label}\n"
        msg += f"📊 [Análise Sofa]({j['link']})\n\n"
    
    msg += "---\n💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
