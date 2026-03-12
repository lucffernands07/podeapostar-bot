import os
import requests
import urllib.parse
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
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_sofa_h2h_corners(driver, t1_name, t2_name):
    """ Regra: Busca o padrão 10/10, 5/5 etc no span do SofaScore """
    query = urllib.parse.quote(f"sofascore h2h {t1_name} vs {t2_name}")
    url_busca = f"https://www.google.com/search?q={query}&btnI"
    try:
        driver.get(url_busca)
        # Espera carregar os cards de estatísticas (spans de confronto)
        wait = WebDriverWait(driver, 10)
        spans = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "textStyle_table")))
        
        for s in spans:
            texto = s.text.lower()
            if "escanteios" in texto and ("menos do que 10.5" in texto or "mais do que 10.5" in texto):
                # Se achou o span, retorna o texto (ex: "Menos do que 10.5 escanteios")
                return "Menos de 10.5" if "menos" in texto else "Mais de 10.5"
    except: pass
    return None

def get_h2h_dupla_chance(t1_id, t2_id):
    """ Regra: Dupla Chance baseada apenas nos ÚLTIMOS 5 confrontos diretos """
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
    """ Regra: Gols e Ambas Marcam baseados nos últimos 10 jogos individuais """
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        o15, btts = 0, 0
        for f in fixtures:
            gh, ga = (f['goals']['home'] or 0), (f['goals']['away'] or 0)
            if (gh + ga) >= 2: o15 += 1
            if gh > 0 and ga > 0: btts += 1
        return (o15 * 10), (btts * 10)
    except: return 0, 0

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
                
                # 1. Regra Escanteio (Scraper H2H Span)
                tipo_canto = get_sofa_h2h_corners(browser, t1['name'], t2['name'])
                
                # 2. Regra Dupla Chance (H2H 5 jogos)
                h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
                
                # 3. Regra Gols (10 jogos individuais)
                h_o15, h_btts = get_individual_stats(t1['id'])
                a_o15, a_btts = get_individual_stats(t2['id'])

                g_info = {"id": m['fixture']['id'], "info": f"*{t1['name']} x {t2['name']}*", "hora": m['fixture']['date'][11:16], "liga": l_nome}

                # --- ADICIONAR AO POOL COM PRIORIDADES ---
                if tipo_canto:
                    pool_entradas.append({"prio": 100, "mkt": f"🔸 {tipo_canto} Escanteios", **g_info})
                
                if h2h_t1 >= 80:
                    pool_entradas.append({"prio": 85, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **g_info})
                elif h2h_t2 >= 80:
                    pool_entradas.append({"prio": 85, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **g_info})

                if (h_o15 + a_o15) / 2 >= 75:
                    pool_entradas.append({"prio": 70, "mkt": "🔸 Mais de 1.5 Gols", **g_info})
        except: continue

    browser.quit()

    # Seleção Final (12 mercados, 3 por jogo)
    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    bilhete, contagem = [], {}
    for e in pool_entradas:
        if len(bilhete) >= 12: break
        mid = e['id']
        contagem[mid] = contagem.get(mid, 0)
        if contagem[mid] < 3:
            bilhete.append(e)
            contagem[mid] += 1

    # Formatação e Envio
    jogos_final = {}
    for e in bilhete:
        if e['id'] not in jogos_final:
            jogos_final[e['id']] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "mkts": []}
        jogos_final[e['id']]["mkts"].append(e['mkt'])

    msg = "🎫 *BILHETE ELITE GLOBAL*\n📊 Regra: H2H (Cantos/DC) + Individual (Gols)\n\n"
    for j in jogos_final.values():
        msg += f"🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n" + "\n".join(j['mkts']) + "\n\n"
    
    enviar_telegram(msg + "---\n💸 [Bet365](https://www.bet365.com)")

if __name__ == "__main__": executar()
