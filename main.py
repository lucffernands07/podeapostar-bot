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
    ligas_config = {2: "Champions", 3: "Europa League", 39: "Premier", 140: "LaLiga", 135: "Serie A", 78: "Bundesliga", 71: "Brasileirão", 203: "Turquia"}
    
    pool_entradas = []

    for l_id, l_nome in ligas_config.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2025"
        try:
            res = requests.get(url, headers=HEADERS).json()
            for m in res.get('response', []):
                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = get_stats(t1['id'])
                a15, a25, abtts, awd = get_stats(t2['id'])
                h2h_t1, h2h_t2 = get_h2h_stats(t1['id'], t2['id'])
                
                link_sofa = f"https://www.google.com/search?q=sofascore+{urllib.parse.quote(t1['name'] + ' vs ' + t2['name'])}&btnI"
                g_info = {"id": m['fixture']['id'], "info": f"*{t1['name']} x {t2['name']}*", "hora": m['fixture']['date'][11:16], "liga": l_nome, "sofa": link_sofa}

                # --- LÓGICA DE ESCANTEIOS (ESTILO SOFASCORE 10/10) ---
                c1, c2 = get_corner_stats(t1['id'], l_id, 2025), get_corner_stats(t2['id'], l_id, 2025)
                soma_c = c1 + c2
                
                # Se soma é baixa ou alta demais, é indício de padrão 5/5, 10/10
                if 0 < soma_c <= 8.5:
                    pool_entradas.append({"prio": 100, "mkt": "🔸 Menos de 10.5 Escanteios", **g_info})
                elif soma_c >= 12.5:
                    pool_entradas.append({"prio": 100, "mkt": "🔸 Mais de 10.5 Escanteios", **g_info})

                # --- OUTROS MERCADOS ---
                if hwd >= 75 and h2h_t1 >= 70: pool_entradas.append({"prio": 85, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **g_info})
                if awd >= 75 and h2h_t2 >= 70: pool_entradas.append({"prio": 85, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **g_info})
                if (h15 + a15)/2 >= 75: pool_entradas.append({"prio": 80, "mkt": "🔸 Mais de 1.5 Gols", **g_info})
                if (h25 + a25)/2 >= 70: pool_entradas.append({"prio": 75, "mkt": "🔸 Mais de 2.5 Gols", **g_info})

        except: continue

    # Seleção Final: Máximo 12 mercados totais, 3 por jogo
    pool_entradas.sort(key=lambda x: x['prio'], reverse=True)
    bilhete, contagem = [], {}
    for e in pool_entradas:
        if len(bilhete) >= 12: break
        mid = e['id']
        contagem[mid] = contagem.get(mid, 0)
        if contagem[mid] < 3:
            bilhete.append(e)
            contagem[mid] += 1

    # Formatação por Jogo
    jogos_final = {}
    for e in bilhete:
        if e['id'] not in jogos_final:
            jogos_final[e['id']] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "sofa": e['sofa'], "mkts": []}
        jogos_final[e['id']]["mkts"].append(e['mkt'])

    msg = "🎫 *BILHETE ELITE GLOBAL*\n📊 Regra: 10/10 Escanteios + H2H\n\n"
    for j in jogos_final.values():
        msg += f"🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n" + "\n".join(j['mkts']) + f"\n📊 [Analisar SofaScore]({j['sofa']})\n\n"
    
    enviar_telegram(msg + "---\n💸 [Bet365](https://www.bet365.com)")

if __name__ == "__main__": executar()
                
