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
API_KEY = os.getenv('X_RAPIDAPI_KEY')
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def log_teste(etapa, msg):
    print(f"🔍 [TESTE {etapa}] {msg}")

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_avg_shots_api(team_id, team_name):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        total_shots = 0
        jogos_com_dados = 0
        for f in fixtures:
            url_s = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f['fixture']['id']}&team={team_id}"
            res_s = requests.get(url_s, headers=HEADERS).json()
            stats = res_s.get('response', [])
            if stats and 'statistics' in stats[0]:
                for s in stats[0]['statistics']:
                    if s['type'] == 'Total Shots' and s['value'] is not None:
                        total_shots += int(s['value'])
                        jogos_com_dados += 1
                        break
            time.sleep(0.4)
        media = total_shots / jogos_com_dados if jogos_com_dados > 0 else 0
        log_teste("CHUTES", f"{team_name}: Média de {media:.2f} chutes (Base: {jogos_com_dados} jogos)")
        return media
    except: return 0

def get_h2h_dupla_chance(t1_id, t2_id, label, last=10):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last={last}"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        t1_wd = 0
        for f in fixtures:
            gh, ga = f['goals']['home'] or 0, f['goals']['away'] or 0
            if (f['teams']['home']['id'] == t1_id and gh >= ga) or (f['teams']['away']['id'] == t1_id and ga >= gh): t1_wd += 1
        perc = (t1_wd / len(fixtures)) * 100 if fixtures else 0
        log_teste("H2H", f"{label}: {perc:.0f}% de Dupla Chance")
        return perc
    except: return 0

def get_over_stats(team_id, team_name, over_val):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        count = sum(1 for f in fixtures if (f['goals']['home'] or 0) + (f['goals']['away'] or 0) > over_val)
        perc = (count / len(fixtures)) * 100 if fixtures else 0
        log_teste("GOLS", f"{team_name} Over {over_val}: {perc:.0f}%")
        return perc
    except: return 0

def testar_jogo_especifico():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    
    match = None
    # CORREÇÃO CRÍTICA: Varre as temporadas para não dar "jogo não encontrado"
    for ano in [2025, 2026]:
        log_teste("BUSCA", f"Verificando temporada {ano}...")
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league=135&season={ano}"
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        
        for f in fixtures:
            if "Juventus" in f['teams']['home']['name'] or "Juventus" in f['teams']['away']['name']:
                match = f
                break
        if match: break

    if not match:
        print(f"❌ Jogo da Juventus não encontrado para o dia {hoje} nas temporadas 2025/2026.")
        return

    t1, t2 = match['teams']['home'], match['teams']['away']
    print(f"\n🏟️ ANALISANDO: {t1['name']} x {t2['name']}")
    print("-" * 50)

    # 1. Teste de Performance (Dupla Chance)
    perf_t1 = get_h2h_dupla_chance(t1['id'], t1['id'], f"Performance {t1['name']}")
    perf_t2 = get_h2h_dupla_chance(t2['id'], t2['id'], f"Performance {t2['name']}")
    
    if perf_t1 >= 70:
        log_teste("FILTRO", f"✅ ENTRARIA em Dupla Chance {t1['name']}")
    else:
        log_teste("FILTRO", f"❌ NÃO ENTRARIA em Dupla Chance (Mínimo 70%)")

    # 2. Teste de Gols
    o15_t1 = get_over_stats(t1['id'], t1['name'], 1.5)
    o15_t2 = get_over_stats(t2['id'], t2['name'], 1.5)
    media_o15 = (o15_t1 + o15_t2) / 2
    
    if o15_t1 >= 85 or media_o15 >= 70:
        log_teste("FILTRO", f"✅ ENTRARIA em Over 1.5 (Média: {media_o15}%)")
    else:
        log_teste("FILTRO", f"❌ NÃO ENTRARIA em Over 1.5")

    # 3. Teste de Chutes
    chutes_t1 = get_avg_shots_api(t1['id'], t1['name'])
    chutes_t2 = get_avg_shots_api(t2['id'], t2['name'])
    print(f"📊 Média Combinada de Chutes: {(chutes_t1 + chutes_t2)/2:.2f}")

    # 4. Selenium (SofaScore)
    browser = configurar_browser()
    log_teste("SOFASCORE", "Buscando link...")
    wait = WebDriverWait(browser, 20)
    try:
        browser.get("https://www.sofascore.com/pt/")
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.send_keys(f"{t1['name']} {t2['name']}")
        time.sleep(5)
        res_link = browser.find_elements(By.XPATH, "//a[contains(@href, '/football/match/')]")
        if res_link:
            print(f"🔗 Link encontrado: {res_link[0].get_attribute('href')}")
    except Exception as e:
        print(f"⚠️ Erro SofaScore: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    testar_jogo_especifico()
