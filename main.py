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

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def get_sofa_h2h_corners(driver, t1_name, t2_name):
    # Ajustei a query para ser mais direta ao ponto
    query = urllib.parse.quote(f"sofascore {t1_name} {t2_name} match")
    url_busca = f"https://www.google.com/search?q={query}"
    url_real_com_id = None
    
    try:
        driver.get(url_busca)
        # 1. Clica no primeiro título (h3) que encontrar no Google
        first_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
        first_link.click()

        # 2. O PULO DO GATO: Espera a URL mudar do Google para o SofaScore
        # Isso garante que pegamos o link com o ID (ex: EgbsWgb)
        try:
            WebDriverWait(driver, 15).until(EC.url_contains("sofascore.com"))
            url_real_com_id = driver.current_url 
            print(f"ID Capturado com Sucesso: {url_real_com_id}")
        except:
            # Se falhar a espera, tenta pegar o que estiver na barra
            url_real_com_id = driver.current_url

        # 3. CLICA NA ABA PARTIDAS
        try:
            # Usei um seletor mais flexível que busca 'Partidas' ou o link interno da aba
            aba = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(., 'Partidas') or contains(@href, 'matches')]"))
            )
            driver.execute_script("arguments[0].click();", aba)
            time.sleep(7) # Espera os cards de estatísticas carregarem
        except: 
            pass
        
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # --- SUA REGRA DE CÁLCULO (MANTIDA) ---
        frequencias = []
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        for m in matches:
            trecho_apos = texto_bruto[m.end() : m.end() + 50]
            frequencia = re.search(r"(\d+)/(\d+)", trecho_apos)
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)

        if len(frequencias) >= 2:
            media = (frequencias[0] + frequencias[1]) / 2
            return "Menos de 10.5 Escanteios", media, url_real_com_id
            
    except Exception as e:
        print(f"Erro na busca Sofa: {e}")
    
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
    ligas = {39: "Premier", 140: "LALIGA", 135: "Serie A", 78: "Bundesliga", 61: "Ligue 1", 203: "Turquia", 307: "Saudi Pro", 94: "Português"}
    
    pool_entradas = []

    for l_id, l_nome in ligas.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2025"
        try:
            res = requests.get(url, headers=HEADERS).json()
            for m in res.get('response', []):
                t1, t2 = m['teams']['home'], m['teams']['away']
                
                tipo_canto, perc_canto, url_real_sofa = get_sofa_h2h_corners(browser, t1['name'], t2['name'])
                link_bilhete = url_real_sofa if url_real_sofa else f"https://www.sofascore.com/search?q={t1['name']}+{t2['name']}"

                g_info = {
                    "id": m['fixture']['id'], 
                    "info": f"*{t1['name']} x {t2['name']}*", 
                    "hora": m['fixture']['date'][11:16], 
                    "liga": l_nome, 
                    "sofa_link": link_bilhete
                }

                if tipo_canto and perc_canto >= 85:
                    pool_entradas.append({"prio": perc_canto, "mkt": tipo_canto, "tipo": "canto", **g_info})

                h2h_t1, h2h_t2 = get_h2h_dupla_chance(t1['id'], t2['id'])
                if h2h_t1 >= 70: pool_entradas.append({"prio": h2h_t1, "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
                if h2h_t2 >= 70: pool_entradas.append({"prio": h2h_t2, "mkt": f"{t2['name']} ou Empate", "tipo": "2x", **g_info})

                h_o15, h_o25 = get_individual_stats(t1['id'])
                a_o15, a_o25 = get_individual_stats(t2['id'])
                m_o15, m_o25 = (h_o15 + a_o15)/2, (h_o25 + a_o25)/2
                if m_o15 >= 70: pool_entradas.append({"prio": m_o15, "mkt": "+1.5 Gols", "tipo": "1.5", **g_info})
                if m_o25 >= 70: pool_entradas.append({"prio": m_o25, "mkt": "+2.5 Gols", "tipo": "2.5", **g_info})
        except Exception as e:
            print(f"Erro na liga {l_nome}: {e}")
            continue
            
    browser.quit()
    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    
    # --- AGRUPAMENTO POR JOGO ---
    jogos_selecionados = {}
    c_canto, c_1x, c_2x, c_25 = 0, 0, 0, 0
    
    for e in pool_entradas:
        mid = e['id']
        if len(jogos_selecionados) >= 10 and mid not in jogos_selecionados: continue
        
        if e['tipo'] == 'canto' and c_canto >= 3: continue
        if e['tipo'] == '2.5' and c_25 >= 2: continue
        if e['tipo'] == '2x' and c_2x >= 1: continue
        if e['tipo'] == '1x' and c_1x >= 3: continue

        if mid not in jogos_selecionados:
            jogos_selecionados[mid] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "link": e['sofa_link'], "mkts": []}
        
        if len(jogos_selecionados[mid]["mkts"]) < 2:
            jogos_selecionados[mid]["mkts"].append(e)
            if e['tipo'] == 'canto': c_canto += 1
            if e['tipo'] == '2.5': c_25 += 1
            if e['tipo'] == '2x': c_2x += 1
            if e['tipo'] == '1x': c_1x += 1

    if not jogos_selecionados: 
        print("Nenhum jogo encontrado.")
        return

    lista_final = sorted(jogos_selecionados.values(), key=lambda x: x['liga'])

    # --- MENSAGEM ---
    ligas_enc = sorted(list(set([j['liga'] for j in lista_final])))
    msg = "🎯 *BILHETE DO DIA (10 JOGOS)*\n💰🍀 *BOA SORTE!!!*\n\n🏟️ *LIGAS ENCONTRADAS:*\n"
    for l in ligas_enc: msg += f"🔹 {l}\n"
    msg += "\n"

    for i, j in enumerate(lista_final, 1):
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        for mkt in j['mkts']:
            if mkt['tipo'] == 'canto': label = f"🚩 {mkt['mkt']} {mkt['prio']:.0f}%"
            elif mkt['tipo'] in ['1x', '2x']: label = f"🛡 {mkt['mkt']} ({mkt['prio']:.0f}%)"
            elif mkt['tipo'] == '2.5': label = f"⚡ {mkt['mkt']} ({mkt['prio']:.0f}%)"
            else: label = f"⚽ {mkt['mkt']} ({mkt['prio']:.0f}%)"
            msg += f"🔸 {label}\n"
        msg += f"📊 [Estatísticas]({j['link']})\n\n"
    
    msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
                         
