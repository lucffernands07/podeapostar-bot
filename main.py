import os
import requests
import time
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO ATUALIZADA (API-SPORTS) --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
# Use o nome da variável que você criar no GitHub Secrets (ex: API_SPORTS_KEY)
API_KEY = os.getenv('API_SPORTS_KEY') 

# Novo Host e Header para acesso direto
HEADERS = {'x-apisports-key': API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

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
    url = f"{BASE_URL}/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        total_shots, jogos_com_dados = 0, 0
        for f in fixtures:
            f_id = f['fixture']['id']
            url_s = f"{BASE_URL}/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_s = requests.get(url_s, headers=HEADERS).json()
            stats_list = res_s.get('response', [])
            if stats_list and 'statistics' in stats_list[0]:
                for s in stats_list[0]['statistics']:
                    if s['type'] == 'Total Shots' and s['value'] is not None:
                        total_shots += int(s['value'])
                        jogos_com_dados += 1
                        break
            time.sleep(6.1) # Pausa para respeitar 10 req/min
        return total_shots / jogos_com_dados if jogos_com_dados > 0 else 0
    except: return 0

def get_h2h_dupla_chance(t1_id, t2_id, last=10):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={t1_id}-{t2_id}&last={last}"
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

def get_over_stats(team_id, over_val):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        count = 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total > over_val: count += 1
        return (count / len(fixtures)) * 100
    except: return 0

def get_id_h2h(driver, t1_name, t2_name):
    try:
        driver.get("https://www.sofascore.com/pt/")
        wait = WebDriverWait(driver, 25)
        try:
            cookies_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Agree')]")
            if cookies_btn: cookies_btn[0].click()
        except: pass
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(8)
        resultados = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/match/')]")
        return resultados[0].get_attribute("href") if resultados else "https://www.sofascore.com/"
    except: return "https://www.sofascore.com/"

def executar():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    ligas = {
        39: "Premier League", 140: "LALIGA", 135: "Serie A", 
        78: "Bundesliga", 61: "Ligue 1", 71: "Brasileirão A", 
        141: "LaLiga 2", 72: "Brasileirão B"
    }

    pool_entradas = []

    for l_id, l_nome in ligas.items():
        for ano in [2025, 2026]:
            url = f"{BASE_URL}/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if not fixtures: continue
                
                for m in fixtures:
                    if m['fixture']['status']['short'] != "NS": continue
                    
                    t1, t2 = m['teams']['home'], m['teams']['away']
                    time.sleep(6.1) # Respeitar rate limit
                    
                    perf_t1 = get_h2h_dupla_chance(t1['id'], t1['id'])
                    time.sleep(6.1)
                    
                    o15_t1 = get_over_stats(t1['id'], 1.5)
                    
                    g_info = {
                        "id": m['fixture']['id'], "t1_id": t1['id'], "t2_id": t2['id'],
                        "t1_name": t1['name'], "t2_name": t2['name'],
                        "info": f"*{t1['name']} x {t2['name']}*", 
                        "hora": datetime.fromisoformat(m['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br).strftime("%H:%M"), 
                        "liga": l_nome
                    }

                    if perf_t1[0] >= 75:
                        pool_entradas.append({"perc": perf_t1[0], "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
                    
                    if o15_t1 >= 80:
                        pool_entradas.append({"perc": o15_t1, "mkt": "+1.5 Gols", "tipo": "1.5", **g_info})
                
                time.sleep(6.1)
                break 
            except: continue
                
    pool_entradas.sort(key=lambda x: x['perc'], reverse=True)
    jogos_selecionados = {}
    browser = configurar_browser()

    for e in pool_entradas[:10]: # Limite de 10 jogos para não estourar cota
        mid = e['id']
        if mid not in jogos_selecionados:
            url_sofa = get_id_h2h(browser, e['t1_name'], e['t2_name'])
            jogos_selecionados[mid] = {
                "info": e['info'], "hora": e['hora'], "liga": e['liga'], "link": url_sofa, "mkts": []
            }
        jogos_selecionados[mid]["mkts"].append(e)

    browser.quit()
    
    if not jogos_selecionados: return

    msg = "🎯 *BILHETE DO DIA (H2H)*\n\n"
    for j in jogos_selecionados.values():
        msg += f"🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        for mkt in j['mkts']:
            msg += f"🔶 {mkt['mkt']} ({mkt['perc']:.0f}%)\n"
        msg += f"📊 [Análise Sofa]({j['link']})\n\n"
    
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
