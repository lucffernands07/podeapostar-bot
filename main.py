import os
import requests
from datetime import datetime, timedelta

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
    """Analisa o retrospecto direto para validar 1X ou X2"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1_id}-{t2_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 50, 50 # Sem histórico = neutro
        
        t1_no_loss, t2_no_loss = 0, 0
        total = len(fixtures)
        
        for f in fixtures:
            gh, ga = f['goals']['home'], f['goals']['away']
            # Verifica se o T1 (Casa do jogo de hoje) não perdeu no H2H
            if (f['teams']['home']['id'] == t1_id and gh >= ga) or (f['teams']['away']['id'] == t1_id and ga >= gh):
                t1_no_loss += 1
            # Verifica se o T2 (Visitante de hoje) não perdeu no H2H
            if (f['teams']['home']['id'] == t2_id and gh >= ga) or (f['teams']['away']['id'] == t2_id and ga >= gh):
                t2_no_loss += 1
                
        return (t1_no_loss / total) * 100, (t2_no_loss / total) * 100
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
            g_h, g_a = (f.get('goals', {}).get('home') or 0), (f.get('goals', {}).get('away') or 0)
            if (g_h + g_a) >= 2: o15 += 1
            if (g_h + g_a) >= 3: o25 += 1
            if g_h > 0 and g_a > 0: btts += 1
            if (f['teams']['home']['id'] == team_id and g_h >= g_a) or \
               (f['teams']['away']['id'] == team_id and g_a >= g_h): wd += 1
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
                    
                    # --- NOVA LÓGICA H2H --- #
                    h2h_t1, h2h_t2 = get_h2h_stats(t1['id'], t2['id'])
                    
                    p15, p25, pbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                    g_info = {"id": m['fixture']['id'], "info": f"*{t1['name']} x {t2['name']}*", "hora": hora.strftime('%H:%M'), "liga": l_nome, "link": f"https://www.adamchoi.co.uk/leagues/{l_slug}"}

                    # Regra de Conflito Seletivo (se ambos forem fortes no geral)
                    jogo_travado = hwd >= 80 and awd >= 80 
                    
                    # Dupla Chance validada pelo H2H (Mínimo 70% de não-derrota no confronto direto)
                    if not jogo_travado:
                        if hwd >= 75 and h2h_t1 >= 70: 
                            pool_entradas.append({"prio": (hwd + h2h_t1)/2, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **g_info})
                        if awd >= 75 and h2h_t2 >= 70: 
                            pool_entradas.append({"prio": (awd + h2h_t2)/2, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **g_info})
                    
                    # Gols e Ambas Marcam (Sempre entram se baterem a meta)
                    if p15 >= 75: pool_entradas.append({"prio": p15, "mkt": "🔸 Mais de 1.5 Gols", **g_info})
                    if p25 >= 70: pool_entradas.append({"prio": p25, "mkt": "🔸 Mais de 2.5 Gols", **g_info})
                    if pbtts >= 70: pool_entradas.append({"prio": pbtts, "mkt": "🔸 Ambas Marcam — Sim", **g_info})
                    
                    # Escanteios (SÓ entra se NÃO for jogo travado)
                    if not jogo_travado:
                        c1, c2 = get_corner_stats(t1['id'], l_id, season), get_corner_stats(t2['id'], l_id, season)
                        if 0 < (c1 + c2) < 10.5:
                            p_corner = 100 - ((c1+c2)*3)
                            pool_entradas.append({"prio": p_corner, "mkt": "🔸 Menos de 9.5 Escanteios", **g_info})
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
            jogos_final[m_id] = {"info": e['info'], "hora": e['hora'], "liga": e['liga'], "link": e['link'], "mercados": []}
        p_str = f"**{int(e['prio'])}%**" if e['prio'] >= 90 else f"{int(e['prio'])}%"
        jogos_final[m_id]["mercados"].append(f"{e['mkt']} — {p_str}")

    msg = f"🎫 *BILHETE TOP ENTRADAS - ELITE GLOBAL*\n📊 Regra: H2H + Filtro de Conflito\n\n"
    for i, j in enumerate(jogos_final.values(), 1):
        tipo = "🔥 *Criar Aposta*" if len(j['mercados']) > 1 else "🎯 *Aposta Simples*"
        msg += f"{i}. 🏟️ {j['info']}\n🕒 {j['hora']} | {j['liga']}\n{tipo}\n" + "\n".join(j['mercados']) + f"\n📊 [Estatísticas]({j['link']})\n\n"
    
    enviar_telegram(msg + "---\nAPOSTAR: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)")

if __name__ == "__main__": executar()
            
