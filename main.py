import os
import requests
import urllib.parse
import time
import re
from datetime import datetime, timedelta
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

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_sofa_h2h_corners(driver, t1_name, t2_name):
    query = urllib.parse.quote(f"sofascore {t1_name} {t2_name} h2h statistics")
    url_busca = f"https://www.google.com/search?q={query}"
    try:
        driver.get(url_busca)
        first_link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
        first_link.click()
        time.sleep(6)
        try:
            aba = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="tab:matches"]')))
            driver.execute_script("arguments[0].click();", aba)
        except: pass
        time.sleep(8)
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        matches = list(re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE))
        percs = []
        for m in matches:
            trecho = texto_bruto[m.end() : m.end() + 50]
            f = re.search(r"(\d+)/(\d+)", trecho)
            if f:
                percs.append((int(f.group(1)) / int(f.group(2))) * 100)
        
        if len(percs) >= 2:
            media_canto = sum(percs) / len(percs)
            return "Menos de 10.5 Escanteios", media_canto
    except: pass
    return None, 0

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
        o15, o25 = 0, 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total >= 2: o15 += 1
            if total >= 3: o25 += 1
        return (o15 * 10), (o25 * 10)
    except: return 0, 0

def executar():
    browser = configurar_browser()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_br.strftime("%Y-%m-%d")
    ligas = {39: "Premier", 140: "LaLiga", 135: "Serie A", 78: "Bundesliga", 61: "Ligue 1", 203: "Turquia", 307: "Saudi Pro", 94: "Portugal"}
    
    pool_entradas = []

    for l_id, l_nome in ligas.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2025"
        try:
            res = requests.get(url, headers=HEADERS).json()
            for m in res.get('response', []):
                t1, t2 = m['teams']['home'], m['teams']['away']
                g_info = {"id": m['fixture']['id'], "info": f"*{t1['name']} x {t2['name']}*", "hora": m['fixture']['date'][11:16], "liga": l_nome}

                # 1. Escanteios (H2H SofaScore %)
                tipo_canto, perc_canto = get_sofa_h2h_corners(browser, t1['name'], t2['name'])
                if tipo_canto and perc_canto >= 70:
                    pool_entradas.append({"prio": perc_canto, "mkt": f"🚩 {tipo_canto}", "tipo": "canto", **g_info})

                # 2. Dupla Chance (H2H %)
                h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
                if h2h_t1 >= 70: pool_entradas.append({"prio": h2h_t1, "mkt": f"🔸 1X ({t1['name']})", "tipo": "1x", **g_info})
                if h2h_t2 >= 70: pool_entradas.append({"prio": h2h_t2, "mkt": f"🔸 X2 ({t2['name']})", "tipo": "2x", **g_info})

                # 3. Gols (Individual 10 jogos %)
                h_o15, h_o25 = get_individual_stats(t1['id'])
                a_o15, a_o25 = get_individual_stats(t2['id'])
                media_o15, media_o25 = (h_o15 + a_o15)/2, (h_o25 + a_o25)/2

                if media_o15 >= 70: pool_entradas.append({"prio": media_o15, "mkt": "🔸 +1.5 Gols", "tipo": "1.5", **g_info})
                if media_o25 >= 70: pool_entradas.append({"prio": media_o25, "mkt": "🔸 +2.5 Gols", "tipo": "2.5", **g_info})
        except: continue
    browser.quit()

    # --- FILTRAGEM POR RANK DE % REAL E LIMITES ---
    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    
    bilhete = []
    cont_jogo, c_canto, c_1x, c_2x, c_25 = {}, 0, 0, 0, 0
    
    for e in pool_entradas:
        if len(bilhete) >= 12: break
        
        # Aplicando suas travas específicas
        if e['tipo'] == 'canto' and c_canto >= 3: continue
        if e['tipo'] == '2.5' and c_25 >= 2: continue
        if e['tipo'] == '2x' and c_2x >= 1: continue
        if e['tipo'] == '1x' and c_1x >= 3: continue
        
        mid = e['id']
        cont_jogo[mid] = cont_jogo.get(mid, 0)
        if cont_jogo[mid] < 3:
            bilhete.append(e)
            cont_jogo[mid] += 1
            if e['tipo'] == 'canto': c_canto += 1
            if e['tipo'] == '2.5': c_25 += 1
            if e['tipo'] == '2x': c_2x += 1
            if e['tipo'] == '1x': c_1x += 1

    # Formatação Final
    jogos_final = {}
    for e in bilhete:
        if e['id'] not in jogos_final:
            jogos_final[e['id']] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "mkts": []}
        jogos_final[e['id']]["mkts"].append(f"{e['mkt']} ({e['prio']:.0f}%)")

    msg = "🎫 *BILHETE ELITE RANKING %*\n📊 Critério: Maior Assertividade Real\n"
    for j in jogos_final.values():
        msg += f"\n🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n" + "\n".join(j['mkts']) + "\n"
    
    enviar_telegram(msg + "\n---\n💸 [Bet365](https://www.bet365.com)")

if __name__ == "__main__": executar()
        
