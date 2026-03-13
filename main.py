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
    """ Usa o Scanner Sniper para validar a regra dos 90% """
    query = urllib.parse.quote(f"sofascore {t1_name} {t2_name} h2h statistics")
    url_busca = f"https://www.google.com/search?q={query}"
    
    try:
        driver.get(url_busca)
        first_link = WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
        first_link.click()

        # Clica na aba Partidas
        time.sleep(5)
        try:
            aba = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            driver.execute_script("arguments[0].click();", aba)
        except: pass
        
        time.sleep(8) # Espera carregar os cards
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # Scanner de Escanteios
        frequencias = []
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        for m in matches:
            trecho_apos = texto_bruto[m.end() : m.end() + 50]
            frequencia = re.search(r"(\d+)/(\d+)", trecho_apos)
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)

        # NOVA REGRA: Prioridade se ambos >= 90%
        if len(frequencias) >= 2:
            if frequencias[0] >= 90 and frequencias[1] >= 90:
                return "Menos de 10.5 (PRIORITÁRIO)", 150 # Peso extra
            elif (frequencias[0] + frequencias[1]) / 2 >= 80:
                return "Menos de 10.5", 100 # Peso normal
    except: pass
    return None, 0

def get_h2h_dupla_chance(t1_id, t2_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last=5"
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
            gh, ga = (f['goals']['home'] or 0), (f['goals']['away'] or 0)
            if (gh + ga) >= 2: o15 += 1
        return (o15 * 10)
    except: return 0

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

def executar():
    browser = configurar_browser()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_br.strftime("%Y-%m-%d")
    ligas = {2: "Champions", 3: "Europa League", 39: "Premier", 140: "LaLiga", 135: "Serie A", 78: "Bundesliga"}
    
    pool_entradas = []

    for l_id, l_nome in ligas.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2025"
        try:
            res = requests.get(url, headers=HEADERS).json()
            for m in res.get('response', []):
                t1, t2 = m['teams']['home'], m['teams']['away']
                
                # 1. Escanteios com Nova Regra de Prioridade
                tipo_canto, peso_canto = get_sofa_h2h_corners(browser, t1['name'], t2['name'])
                
                # 2. Dupla Chance
                h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
                
                # 3. Gols
                h_o15 = get_individual_stats(t1['id'])
                a_o15 = get_individual_stats(t2['id'])

                g_info = {"id": m['fixture']['id'], "info": f"*{t1['name']} x {t2['name']}*", "hora": m['fixture']['date'][11:16], "liga": l_nome}

                # Adiciona ao Pool respeitando os pesos
                if tipo_canto:
                    pool_entradas.append({"prio": peso_canto, "mkt": f"🚩 {tipo_canto}", **g_info})
                
                if h2h_t1 >= 80:
                    pool_entradas.append({"prio": 85, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **g_info})
                elif h2h_t2 >= 80:
                    pool_entradas.append({"prio": 85, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **g_info})

                if (h_o15 + a_o15) / 2 >= 80:
                    pool_entradas.append({"prio": 70, "mkt": "🔸 Mais de 1.5 Gols", **g_info})
        except: continue

    browser.quit()

    # Seleção Final: Máximo 12 mercados, máximo 3 por partida
    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    bilhete, contagem = [], {}
    for e in pool_entradas:
        if len(bilhete) >= 12: break
        mid = e['id']
        contagem[mid] = contagem.get(mid, 0)
        if contagem[mid] < 3:
            bilhete.append(e)
            contagem[mid] += 1

    # Formatação Final
    jogos_final = {}
    for e in bilhete:
        if e['id'] not in jogos_final:
            jogos_final[e['id']] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "mkts": []}
        jogos_final[e['id']]["mkts"].append(e['mkt'])

    msg = "🎫 *BILHETE ELITE GLOBAL*\n🔥 Foco: Escanteios 90%+ (Prioridade)\n\n"
    for j in jogos_final.values():
        msg += f"🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n" + "\n".join(j['mkts']) + "\n\n"
    
    enviar_telegram(msg + "---\n💸 [Bet365](https://www.bet365.com)")

if __name__ == "__main__": executar()
