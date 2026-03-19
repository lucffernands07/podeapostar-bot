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

def get_avg_shots_api(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        total_shots, count = 0, 0
        for f in fixtures:
            f_id = f['fixture']['id']
            url_s = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_s = requests.get(url_s, headers=HEADERS).json()
            stats = res_s.get('response', [])
            if stats:
                for s in stats[0].get('statistics', []):
                    if s['type'] == 'Total Shots':
                        total_shots += (int(s['value']) if s['value'] else 0)
                        count += 1
                        break
            time.sleep(0.2)
        return total_shots / count if count > 0 else 0
    except: return 0

def get_id_h2h(driver, t1_name, t2_name):
    url_real = "https://www.sofascore.com/"
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
        
        resultados = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/match/')]")
        if resultados:
            url_real = resultados[0].get_attribute("href")
    except: pass
    return url_real

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

    LIGAS_MATA_MATA = [2, 11, 13]
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
            
            g_info = {
                "id": m['fixture']['id'], 
                "t1_id": t1['id'], "t2_id": t2['id'],
                "t1_name": t1['name'], "t2_name": t2['name'],
                "info": f"*{t1['name']} x {t2['name']}*", 
                "hora": hora_br, 
                "liga": l_nome
            }

            h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
            if h2h_t1 >= 80: 
                pool_entradas.append({"perc": h2h_t1, "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
            if h2h_t2 >= 90 and l_id not in LIGAS_MATA_MATA: 
                pool_entradas.append({"perc": h2h_t2, "mkt": f"{t2['name']} ou Empate", "tipo": "2x", **g_info})

            m_o15 = (get_individual_stats(t1['id']) + get_individual_stats(t2['id'])) / 2
            if m_o15 >= 70: 
                pool_entradas.append({"perc": m_o15, "mkt": "+1.5 Gols", "tipo": "1.5", **g_info})
                
    pool_entradas.sort(key=lambda x: x['perc'], reverse=True)
    jogos_selecionados = {}
    total_mercados = 0 

    browser = configurar_browser()

    for e in pool_entradas:
        mid = e['id']
        if total_mercados >= 13: break
        if mid not in jogos_selecionados and len(jogos_selecionados) >= 10: continue
            
        if mid not in jogos_selecionados:
            url_sofa = get_id_h2h(browser, e['t1_name'], e['t2_name'])
            m_chutes = (get_avg_shots_api(e['t1_id']) + get_avg_shots_api(e['t2_id'])) / 2
            
            jogos_selecionados[mid] = {
                "info": e['info'], "hora": e['hora'], "liga": e['liga'], 
                "link": url_sofa, "media_chutes": m_chutes, "mkts": []
            }
        
        if len(jogos_selecionados[mid]["mkts"]) < 3 and total_mercados < 13:
            jogos_selecionados[mid]["mkts"].append(e)
            total_mercados += 1

    browser.quit()

    jogos_selecionados = {k: v for k, v in jogos_selecionados.items() if v["mkts"]}
    if not jogos_selecionados: return
    lista_final = sorted(jogos_selecionados.values(), key=lambda x: x['liga'])

    # MENSAGEM FINAL
    msg = "🎯 *BILHETE DO DIA (SISTEMA H2H)*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, j in enumerate(lista_final, 1):
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        
        # 1. MERCADOS PRINCIPAIS (1x, 2x, +1.5) primeiro
        j['mkts'].sort(key=lambda x: x['perc'], reverse=True)
        for mkt in j['mkts']:
            label = "🛡️" if mkt['tipo'] in ['1x', '2x'] else "⚽"
            msg += f"🔶 {label} {mkt['mkt']} ({mkt['perc']:.0f}%)\n"

        # 2. DICA DE ESCANTEIO depois com a média final
        media_c = j.get('media_chutes', 0)
        if 0 < media_c <= 10.5:
            msg += f"💡 *Dica:* Menos 10.5 Escanteios ({media_c:.1f} chutes)\n"
        
        msg += f"📊 [Análise Sofa]({j['link']})\n\n"
    
    msg += "---\n💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
