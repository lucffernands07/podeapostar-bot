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
    # Alterado para os últimos 5 jogos individuais
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        total_shots, jogos_com_dados = 0, 0
        for f in fixtures:
            f_id = f['fixture']['id']
            url_s = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_s = requests.get(url_s, headers=HEADERS).json()
            stats_list = res_s.get('response', [])
            if stats_list and 'statistics' in stats_list[0]:
                for s in stats_list[0]['statistics']:
                    if s['type'] == 'Total Shots' and s['value'] is not None:
                        total_shots += int(s['value'])
                        jogos_com_dados += 1
                        break
            time.sleep(0.4)
        return total_shots / jogos_com_dados if jogos_com_dados > 0 else 0
    except: return 0

def get_h2h_dupla_chance(t1_id, t2_id, last=5):
    # Alterado para os últimos 5 jogos (H2H ou Individual)
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last={last}"
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
    # Alterado para os últimos 5 jogos individuais
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5"
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
        if resultados: url_real = resultados[0].get_attribute("href")
    except: pass
    return url_real

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
                if res.get('response'): fixtures_hoje.extend(res['response'])
            except: continue
            
        for m in fixtures_hoje:
            if m['fixture']['status']['short'] != "NS": continue

            t1, t2 = m['teams']['home'], m['teams']['away']
            
            # PERFORMANCE ATUAL (Últimos 5 jogos individuais via função H2H)
            perf_t1 = get_h2h_dupla_chance(t1['id'], t1['id'], last=5)
            perf_t2 = get_h2h_dupla_chance(t2['id'], t2['id'], last=5)
            
            # CONFRONTO DIRETO (Últimos 5 jogos)
            h2h_dir_5_t1, h2h_dir_5_t2 = get_h2h_dupla_chance(t1['id'], t2['id'], last=5)

            g_info = {
                "id": m['fixture']['id'], "t1_id": t1['id'], "t2_id": t2['id'],
                "t1_name": t1['name'], "t2_name": t2['name'],
                "info": f"*{t1['name']} x {t2['name']}*", 
                "hora": datetime.fromisoformat(m['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br).strftime("%H:%M"), 
                "liga": l_nome
            }

            # --- REGRAS DE VITÓRIA / EMPATE ---
            if l_id not in LIGAS_MATA_MATA:
                if perf_t1[0] >= 70 and perf_t2[1] <= 70:
                    pool_entradas.append({"perc": perf_t1[0], "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
                elif perf_t2[1] >= 90 and perf_t1[0] <= 60:
                    pool_entradas.append({"perc": perf_t2[1], "mkt": f"{t2['name']} ou Empate", "tipo": "2x", **g_info})
                elif h2h_dir_5_t1 >= 80:
                    pool_entradas.append({"perc": h2h_dir_5_t1, "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
            else:
                if h2h_dir_5_t1 >= 100:
                    pool_entradas.append({"perc": 100, "mkt": f"{t1['name']} ou Empate", "tipo": "1x", **g_info})
                elif h2h_dir_5_t2 >= 100:
                    pool_entradas.append({"perc": 100, "mkt": f"{t2['name']} ou Empate", "tipo": "2x", **g_info})

            # --- REGRAS DE GOLS ---
            o15_t1, o15_t2 = get_over_stats(t1['id'], 1.5), get_over_stats(t2['id'], 1.5)
            o25_t1, o25_t2 = get_over_stats(t1['id'], 2.5), get_over_stats(t2['id'], 2.5)
            m_o15 = (o15_t1 + o15_t2) / 2
            
            # Ajustado para >= 80% individual conforme pedido
            if o15_t1 >= 80 or m_o15 >= 70:
                pool_entradas.append({"perc": max(o15_t1, m_o15), "mkt": "+1.5 Gols", "tipo": "1.5", **g_info})
            
            if (o25_t1 >= 80 and o25_t2 >= 60) or (o25_t2 >= 80 and o25_t1 >= 60):
                m_o25 = (o25_t1 + o25_t2) / 2
                pool_entradas.append({"perc": m_o25, "mkt": "+2.5 Gols", "tipo": "2.5", **g_info})
                
    pool_entradas.sort(key=lambda x: x['perc'], reverse=True)
    jogos_selecionados = {}
    total_mercados = 0 
    browser = configurar_browser()

    for e in pool_entradas:
        mid = e['id']
        if total_mercados >= 13: break # Limite de 13 mercados no bilhete
            
        if mid not in jogos_selecionados:
            url_sofa = get_id_h2h(browser, e['t1_name'], e['t2_name'])
            chutes_t1 = get_avg_shots_api(e['t1_id'])
            time.sleep(0.4)
            chutes_t2 = get_avg_shots_api(e['t2_id'])
            jogos_selecionados[mid] = {
                "info": e['info'], "hora": e['hora'], "liga": e['liga'], "link": url_sofa, 
                "media_chutes": (chutes_t1 + chutes_t2) / 2, "mkts": []
            }
        
        # Limite de 3 mercados por jogo
        if len(jogos_selecionados[mid]["mkts"]) < 3 and total_mercados < 13:
            jogos_selecionados[mid]["mkts"].append(e)
            total_mercados += 1

    browser.quit()
    jogos_finais = sorted(jogos_selecionados.values(), key=lambda x: x['liga'])
    if not jogos_finais: return

    msg = "🎯 *BILHETE DO DIA (SISTEMA H2H)*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, j in enumerate(jogos_finais, 1):
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n"
        j['mkts'].sort(key=lambda x: x['perc'], reverse=True)
        for mkt in j['mkts']:
            label = "🛡️" if mkt['tipo'] in ['1x', '2x'] else "🔥" if mkt['tipo'] == "2.5" else "⚽"
            msg += f"🔶 {label} {mkt['mkt']} ({mkt['perc']:.0f}%)\n"
        if j.get('media_chutes', 0) > 0:
            msg += f"💡 *Média Escanteios:* ({j['media_chutes']:.1f})\n"
        msg += f"📊 [Análise Sofa]({j['link']})\n\n"
    
    msg += "---\n💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
