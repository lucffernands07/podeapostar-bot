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

# --- CONFIGURAÇÃO (AJUSTADA PARA API-SPORTS) --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('API_SPORTS_KEY')  # Usando sua variável do Git
# No site original (API-Sports), o header obrigatório é 'x-apisports-key'
HEADERS = {'x-apisports-key': API_KEY}
URL_BASE = "https://v3.football.api-sports.io"

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
    # Mudança para URL da API-Sports
    url = f"{URL_BASE}/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        total_shots = 0
        jogos_com_dados = 0
        for f in fixtures:
            f_id = f['fixture']['id']
            url_s = f"{URL_BASE}/fixtures/statistics?fixture={f_id}&team={team_id}"
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
        log_teste("CHUTES", f"{team_name}: Média de {media:.2f} chutes")
        return media
    except: return 0

def get_h2h_dupla_chance(t1_id, t2_id, label, last=10):
    url = f"{URL_BASE}/fixtures/headtohead?h2h={t1_id}-{t2_id}&last={last}"
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

def testar_juventus_direto():
    log_teste("BUSCA", "Iniciando Busca na API-Sports via ID da Juventus (496)...")
    
    # Busca o próximo jogo da Juventus (ID 496)
    url = f"{URL_BASE}/fixtures?team=496&next=1"
    
    try:
        res = requests.get(url, headers=HEADERS).json()
        # Log para conferir se a API-Sports aceitou sua chave
        if 'errors' in res and res['errors']:
            print(f"❌ ERRO DE AUTENTICAÇÃO: {res['errors']}")
            return

        fixtures = res.get('response', [])
        if not fixtures:
            log_teste("ERRO", "Nenhum jogo encontrado para a Juventus. Verifique sua conta na API-Sports.")
            return

        match = fixtures[0]
        t1, t2 = match['teams']['home'], match['teams']['away']
        print(f"\n🏟️  JOGO ENCONTRADO: {t1['name']} x {t2['name']}")
        print(f"📅  ID do Jogo: {match['fixture']['id']}")
        print("-" * 50)

        # 1. Teste Dupla Chance
        perf_t1 = get_h2h_dupla_chance(t1['id'], t1['id'], f"Performance {t1['name']}")
        
        # 2. Teste Chutes
        chutes_t1 = get_avg_shots_api(t1['id'], t1['name'])
        
        # 3. SofaScore
        browser = configurar_browser()
        log_teste("SOFASCORE", "Buscando link...")
        browser.get("https://www.sofascore.com/pt/")
        wait = WebDriverWait(browser, 20)
        try:
            search = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
            search.send_keys(f"{t1['name']} {t2['name']}")
            time.sleep(5)
            res_link = browser.find_elements(By.XPATH, "//a[contains(@href, '/football/match/')]")
            if res_link:
                print(f"🔗 Link encontrado: {res_link[0].get_attribute('href')}")
        except: print("⚠️ Link não encontrado no SofaScore.")
        browser.quit()

    except Exception as e:
        print(f"❌ Erro Geral: {e}")

if __name__ == "__main__":
    testar_juventus_direto()
