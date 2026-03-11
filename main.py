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

def get_corner_avg(team_id, league_id, season):
    """Busca a média de escanteios (Igual ao dado do Sofascore)"""
    try:
        url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?season={season}&team={team_id}&league={league_id}"
        res = requests.get(url, headers=HEADERS, timeout=7).json()
        avg = float(res.get('response', {}).get('corners', {}).get('avg', 0) or 0)
        return avg
    except: return 0

def get_adamchoi_stats(team_id):
    """Analisa os últimos 10 jogos reais (Tendência de Gols e Dupla Chance)"""
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
    
    # LISTA DE LIGAS FOCO (Sua lista de Elite)
    ligas_config = {
        2: ("Champions League", "uefa-champions-league"),
        3: ("Europa League", "uefa-europa-league"),
        39: ("Premier League", "england-premier-league"),
        40: ("Championship", "england-championship"),
        140: ("LaLiga", "spain-la-liga"),
        135: ("Serie A", "italy-serie-a"),
        78: ("Bundesliga", "germany-bundesliga"),
        94: ("Português", "portugal-primeira-liga"),
        88: ("Holandês", "netherlands-eredivisie"),
        71: ("Brasileirão A", "brazil-serie-a"),
        268: ("Argentina", "argentina-primera-division"),
        203: ("Turquia", "turkish-super-lig")
    }
    
    pre_ranking = []

    # FASE 1: SCANNER GLOBAL DE GOLS E RESULTADOS
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
                    h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                    a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                    m15, m25 = (h15+a15)/2, (h25+a25)/2

                    game_data = {
                        "id": m['fixture']['id'], 
                        "info": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora.strftime('%H:%M')}",
                        "l_id": l_id, "season": m['league']['season'], "t1": t1['id'], "t2": t2['id'], 
                        "liga": l_nome, "link": f"https://www.adamchoi.co.uk/leagues/{l_slug}"
                    }

                    # Critérios de entrada (Mínimo 75% para garantir volume)
                    if hwd >= 75: pre_ranking.append({"prio": hwd+10, "mkt": f"🔸 1X ({t1['name']} ou Empate)", **game_data})
                    elif awd >= 75: pre_ranking.append({"prio": awd+10, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", **game_data})
                    if m25 >= 75: pre_ranking.append({"prio": m25+5, "mkt": "🔸 Mais de 2.5 Gols", **game_data})
                    elif m15 >= 75: pre_ranking.append({"prio": m15, "mkt": "🔸 Mais de 1.5 Gols", **game_data})
                break
            except: continue

    # FASE 2: SELECIONA AS 8 MELHORES (Máx 2 por jogo)
    pre_ranking.sort(key=lambda x: x['prio'], reverse=True)
    selecoes_8 = []
    jogos_contagem = {}
    for s in pre_ranking:
        if len(selecoes_8) >= 8: break
        m_id = s['id']
        jogos_contagem[m_id] = jogos_contagem.get(m_id, 0)
        if jogos_contagem[m_id] < 2:
            selecoes_8.append(s)
            jogos_contagem[m_id] += 1

    # FASE 3: POLIMENTO DE ESCANTEIOS (Até completar 12 entradas)
    bilhete_final = list(selecoes_8)
    jogos_ja_no_bilhete = {s['id'] for s in selecoes_8}
    
    for s in selecoes_8:
        if len(bilhete_final) >= 12: break
        
        # Só busca escanteio se o jogo for promissor
        c1 = get_corner_avg(s['t1'], s['l_id'], s['season'])
        c2 = get_corner_avg(s['t2'], s['l_id'], s['season'])
        
        # Se a média somada for baixa (estilo Sofascore), adiciona
        if 0 < (c1 + c2) < 10.5:
            bilhete_final.append({
                "mkt": "🔸 Menos de 9.5 Escanteios (-9.5)", 
                "id": s['id'], "info": s['info'], "liga": s['liga'], "link": s['link']
            })

    # AGRUPAMENTO E ENVIO
    jogos_agrupados = {}
    for s in bilhete_final:
        m_id = s['id']
        if m_id not in jogos_agrupados:
            jogos_agrupados[m_id] = {"info": s['info'], "liga": s['liga'], "mercados": [], "link": s['link']}
        jogos_agrupados[m_id]["mercados"].append(s['mkt'])

    msg = f"🎫 *BILHETE DE ELITE - TOP APOSTAS ({hoje})*\n🎯 12 Entradas (8 Elite + 4 Cantos Cirúrgicos)\n\n"
    for i, (m_id, j) in enumerate(jogos_agrupados.items(), 1):
        tipo = "🔥 *Criar Aposta*" if len(j['mercados']) > 1 else "🎯 *Aposta Simples*"
        msg += f"{i}. {j['info']} | {j['liga']}\n{tipo}\n" + "\n".join(j['mercados']) + f"\n📊 [Estatísticas]({j['link']})\n\n"
    
    msg += "---\nAPOSTAR: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar()
                                   
