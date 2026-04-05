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

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('API_SPORTS_KEY') 
HEADERS = {'x-apisports-key': API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

def log(tag, msg):
    print(f"LOG: [{tag}] {msg}")

def configurar_browser():
    log("SISTEMA", "Configurando Browser Headless...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0...")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
        log("TELEGRAM", "Bilhete enviado com sucesso!")
    except Exception as e:
        log("ERRO", f"Falha ao enviar Telegram: {e}")

def get_h2h_dupla_chance(t1_id, t1_name, last=10):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={t1_id}-{t1_id}&last={last}"
    try:
        log("API", f"Calculando desempenho recente: {t1_name}")
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0
        t1_wd = sum(1 for f in fixtures if (f['teams']['home']['id'] == t1_id and f['goals']['home'] >= f['goals']['away']) or (f['teams']['away']['id'] == t1_id and f['goals']['away'] >= f['goals']['home']))
        return (t1_wd / len(fixtures)) * 100, 0
    except: return 0, 0

def get_over_stats(team_id, team_name, over_val):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=10"
    try:
        log("API", f"Analisando Over {over_val}: {team_name}")
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        count = sum(1 for f in fixtures if (f['goals']['home'] or 0) + (f['goals']['away'] or 0) > over_val)
        return (count / len(fixtures)) * 100
    except: return 0

def get_id_h2h(driver, t1_name, t2_name):
    try:
        log("SOFASCORE", f"Buscando link de análise: {t1_name} x {t2_name}")
        driver.get("https://www.sofascore.com/pt/")
        wait = WebDriverWait(driver, 20)
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(7)
        resultados = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/match/')]")
        return resultados[0].get_attribute("href") if resultados else "SofaLink não encontrado"
    except: return "https://www.sofascore.com/"

def executar():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    log("INÍCIO", f"Executando MAIN.PY - {hoje}")
    
    ligas = {39: "Premier League", 140: "LALIGA", 135: "Serie A", 78: "Bundesliga", 61: "Ligue 1", 71: "Brasileirão A", 141: "LaLiga 2", 72: "Brasileirão B"}
    pool_entradas = []

    for l_id, l_nome in ligas.items():
        log("LIGA", f"Explorando: {l_nome} (ID: {l_id})")
        for ano in [2025, 2026]:
            url = f"{BASE_URL}/fixtures?date={hoje}&league={l_id}&season={ano}"
            res = requests.get(url, headers=HEADERS).json()
            fixtures = res.get('response', [])
            if not fixtures: continue
            
            for m in fixtures:
                if m['fixture']['status']['short'] != "NS": continue
                t1, t2 = m['teams']['home'], m['teams']['away']
                
                time.sleep(6.1)
                perf_t1, _ = get_h2h_dupla_chance(t1['id'], t1['name'])
                time.sleep(6.1)
                o15_t1 = get_over_stats(t1['id'], t1['name'], 1.5)
                
                g_info = {
                    "id": m['fixture']['id'], "t1_name": t1['name'], "t2_name": t2['name'],
                    "info": f"*{t1['name']} x {t2['name']}*", "liga": l_nome,
                    "hora": datetime.fromisoformat(m['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br).strftime("%H:%M")
                }

                if perf_t1 >= 75:
                    log("FILTRO", f"Vantagem Casa: {t1['name']} ({perf_t1}%)")
                    pool_entradas.append({"perc": perf_t1, "mkt": f"{t1['name']} ou Empate", **g_info})
                if o15_t1 >= 80:
                    log("FILTRO", f"Over 1.5 detectado: {t1['name']} ({o15_t1}%)")
                    pool_entradas.append({"perc": o15_t1, "mkt": "+1.5 Gols", **g_info})
            break 
                
    if not pool_entradas:
        log("FIM", "Nenhum jogo atendeu aos critérios do Main hoje.")
        return

    pool_entradas.sort(key=lambda x: x['perc'], reverse=True)
    jogos_selecionados = {}
    browser = configurar_browser()

    for e in pool_entradas[:10]:
        mid = e['id']
        if mid not in jogos_selecionados:
            url_sofa = get_id_h2h(browser, e['t1_name'], e['t2_name'])
            jogos_selecionados[mid] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "link": url_sofa, "mkts": []}
        jogos_selecionados[mid]["mkts"].append(e)

    browser.quit()
    
    msg = "🎯 *BILHETE DO DIA (H2H)*\n\n"
    for j in jogos_selecionados.values():
        msg += f"🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        for mkt in j['mkts']:
            msg += f"🔶 {mkt['mkt']} ({mkt['perc']:.0f}%)\n"
        msg += f"📊 [Análise Sofa]({j['link']})\n\n"
    
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
