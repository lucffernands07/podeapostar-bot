import os
import requests
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

def get_h2h_stats(t1_id, t2_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 50, 50
        t1_nl, t2_nl = 0, 0
        total = len(fixtures)
        for f in fixtures:
            gh, ga = f['goals']['home'], f['goals']['away']
            if (f['teams']['home']['id'] == t1_id and gh >= ga) or (f['teams']['away']['id'] == t1_id and ga >= gh): t1_nl += 1
            if (f['teams']['home']['id'] == t2_id and gh >= ga) or (f['teams']['away']['id'] == t2_id and ga >= gh): t2_nl += 1
        return (t1_nl / total) * 100, (t2_nl / total) * 100
    except: return 50, 50

def get_corner_stats(team_id, league_id, season):
    try:
        url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?season={season}&team={team_id}&league={league_id}"
        res = requests.get(url, headers=HEADERS, timeout=7).json()
        return float(res.get('response', {}).get('corners', {}).get('avg', 0) or 0)
    except: return 0

def get_stats(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0
        o15, o25, btts, wd = 0, 0, 0, 0
        for f in fixtures:
            gh, ga = (f.get('goals', {}).get('home') or 0), (f.get('goals', {}).get('away') or 0)
            if (gh + ga) >= 2: o15 += 1
            if (gh + ga) >= 3: o25 += 1
            if gh > 0 and ga > 0: btts += 1
            if (f['teams']['home']['id'] == team_id and gh >= ga) or (f['teams']['away']['id'] == team_id and ga >= gh): wd += 1
        return (o15*10), (o25*10), (btts*10), (wd*10)
    except: return 0, 0, 0, 0

def executar():
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    ligas_config = {
        2: ("Champions League", "uefa-champions-league"), 3: ("Europa League", "uefa-europa-league"),
        39: ("Premier League", "england-premier-league"), 40: ("Championship", "england-championship"),
        140: ("LaLiga", "spain-la-liga"), 135: ("Serie A", "italy-serie-a"),
        78: ("Bundesliga", "germany-bundesliga"), 94: ("Português", "portugal-primeira-liga"),
        88: ("Holandês", "netherlands-eredivisie"), 71: ("Brasileirão A", "brazil-serie-a"),
        268: ("Argentina", "argentina-primera-division"), 203: ("Turquia", "turkish-super-lig")
    }
    
    pool_entradas = []

    for l_id, (l_nome, l_slug) in ligas_config.items():
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                games = res.get('response', [])
                if not games: continue
                
                for m in games:
                    hora = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
                    if hora < agora_br: continue
                    
                    t1, t2 = m['teams']['home'], m['teams']['away']
                    h15, h25, hbtts, hwd = get_stats(t1['id'])
                    a15, a25, abtts, awd = get_stats(t2['id'])
                    h2h_t1, h2h_t2 = get_h2h_stats(t1['id'], t2['id'])
                    
                    p15, p25, pbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                    
                    # Gerar link de busca do SofaScore focado no confronto
                    query_sofa = urllib.parse.quote(f"site:sofascore.com {t1['name']} vs {t2['name']}")
                    link_sofa = f"https://www.google.com/search?q={query_sofa}&btnI"

                    g_info = {
                        "id": m['fixture']['id'], 
                        "info": f"*{t1['name']} x {t2['name']}*", 
                        "hora": hora.strftime('%H:%M'), 
                        "liga": l_nome, 
                        "link_sofa": link_sofa
                    }

                    # --- 1. DUPLA CHANCE (VETO H2H) ---
                    jogo_travado = hwd >= 80 and awd >= 80 
                    if not jogo_travado:
                        if hwd >= 75 and h2h_t1 >= 70: 
                            pool_entradas.append({"prio": (hwd + h2h_t1)/2, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **g_info})
                        if awd >= 75 and h2h_t2 >= 70: 
                            pool_entradas.append({"prio": (awd + h2h_t2)/2, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **g_info})
                    
                    # --- 2. GOLS ---
                    if p15 >= 75: pool_entradas.append({"prio": p15, "mkt": "🔸 Mais de 1.5 Gols", **g_info})
                    if p25 >= 70: pool_entradas.append({"prio": p25, "mkt": "🔸 Mais de 2.5 Gols", **g_info})
                    if pbtts >= 70: pool_entradas.append({"prio": pbtts, "mkt": "🔸 Ambas Marcam — Sim", **g_info})
                    
                    # --- 3. ESCANTEIOS (TRAVA 5/5 + VETO CONFLITO) ---
                    c1, c2 = get_corner_stats(t1['id'], l_id, season), get_corner_stats(t2['id'], l_id, season)
                    soma_c = c1 + c2
                    conflito_escanteio = (c1 >= 6.0 and c2 <= 3.5) or (c2 >= 6.0 and c1 <= 3.5)

                    if not jogo_travado and not conflito_escanteio:
                        if soma_c >= 12.0:
                            pool_entradas.append({"prio": 95, "mkt": "🔸 Mais de 10.5 Escanteios", **g_info})
                        elif 0 < soma_c <= 8.8:
                            pool_entradas.append({"prio": 95, "mkt": "🔸 Menos de 10.5 Escanteios", **g_info})
                break
            except: continue

    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    bilhete_final, contagem_por_jogo = [], {}
    for e in pool_entradas:
        if len(bilhete_final) >= 12: break
        m_id = e['id']
        contagem_por_jogo[m_id] = contagem_por_jogo.get(m_id, 0)
        if contagem_por_jogo[m_id] < 3:
            bilhete_final.append(e)
            contagem_por_jogo[m_id] += 1

    jogos_final = {}
    for e in bilhete_final:
        m_id = e['id']
        if m_id not in jogos_final:
            jogos_final[m_id] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "sofa": e['link_sofa'], "mercados": []}
        p_str = f"**{int(e['prio'])}%**" if e['prio'] >= 90 else f"{int(e['prio'])}%"
        jogos_final[m_id]["mercados"].append(f"{e['mkt']} — {p_str}")

    msg = f"🎫 *BILHETE ELITE GLOBAL*\n📊 Regra: H2H + Trava 5/5 SofaScore\n\n"
    for i, j in enumerate(jogos_final.values(), 1):
        tipo = "🔥 *Criar Aposta*" if len(j['mercados']) > 1 else "🎯 *Aposta Simples*"
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n{tipo}\n" + "\n".join(j['mercados'])
        msg += f"\n📊 [Analisar no SofaScore]({j['sofa']})\n\n"
    
    enviar_telegram(msg + "---\nAPOSTAR: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)")

if __name__ == "__main__": executar()
                
