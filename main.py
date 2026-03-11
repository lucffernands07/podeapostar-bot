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
    try:
        requests.post(url, json=payload, timeout=15)
        print("✅ Bilhete de Elite enviado!")
    except: print("❌ Erro Telegram")

def get_corner_stats(team_id):
    """Média de escanteios ultra-rápida (Busca na temporada atual)"""
    try:
        # Tenta 2026 (Brasil/SulAmericana) e 2025 (Europa)
        for s in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?season={s}&team={team_id}&league=71"
            res = requests.get(url, headers=HEADERS, timeout=5).json()
            avg = float(res.get('response', {}).get('corners', {}).get('avg', 0) or 0)
            if avg > 0: return avg
        return 0
    except: return 0

def get_adamchoi_stats(team_id):
    """Analisa a forma real dos últimos 10 jogos (Independente de Liga/Ano)"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0
        o15, o25, btts, wd = 0, 0, 0, 0
        for f in fixtures:
            g_h, g_a = (f['goals']['home'] or 0), (f['goals']['away'] or 0)
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
    
    # LISTA EXPANDIDA DE LIGAS (Mundo Inteiro)
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
        262: ("México", "mexico-liga-mx"),
        239: ("Colômbia", "colombia-primera-a"),
        203: ("Turquia", "turkish-super-lig")
    }
    
    ranking_geral = []

    for l_id, (l_nome, l_slug) in ligas_config.items():
        # TESTA AS DUAS TEMPORADAS PARA CADA LIGA
        jogos_da_liga = []
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                if res.get('response'):
                    jogos_da_liga = res.get('response')
                    break # Se achou jogos em uma season, não precisa da outra
            except: continue

        for m in jogos_da_liga:
            hora_jogo = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
            if hora_jogo < agora_br: continue

            t1, t2 = m['teams']['home'], m['teams']['away']
            h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
            a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
            
            m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
            match_id = m['fixture']['id']
            match_info = f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora_jogo.strftime('%H:%M')}"
            link = f"https://www.adamchoi.co.uk/leagues/{l_slug}"

            # REGRAS E PRIORIDADES
            # 1. Dupla Chance
            if hwd >= 85: ranking_geral.append({"prio": hwd + 10, "mkt": f"🔸 1X ({t1['name']} ou Empate)", "id": match_id, "info": match_info, "liga": l_nome, "link": link})
            elif awd >= 85: ranking_geral.append({"prio": awd + 10, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", "id": match_id, "info": match_info, "liga": l_nome, "link": link})
            
            # 2. Gols
            if m25 >= 85: ranking_geral.append({"prio": m25 + 5, "mkt": "🔸 Mais de 2.5 Gols", "id": match_id, "info": match_info, "liga": l_nome, "link": link})
            elif m15 >= 80: ranking_geral.append({"prio": m15, "mkt": "🔸 Mais de 1.5 Gols", "id": match_id, "info": match_info, "liga": l_nome, "link": link})
            
            # 3. Escanteios (Proteção Contra "Abafas" - Foto Bodo/Sporting)
            if m15 >= 85:
                try:
                    c1 = get_corner_stats(t1['id'])
                    c2 = get_corner_stats(t2['id'])
                    if 0 < (c1 + c2) < 10.5:
                        ranking_geral.append({"prio": 83, "mkt": "🔸 Menos de 9.5 Escanteios (-9.5)", "id": match_id, "info": match_info, "liga": l_nome, "link": link})
                except: pass

            # 4. Ambas Marcam
            if mbtts >= 80: ranking_geral.append({"prio": mbtts + 2, "mkt": "🔸 Ambas Marcam — Sim", "id": match_id, "info": match_info, "liga": l_nome, "link": link})

    if ranking_geral:
        # SELECIONA AS 12 MELHORES DO MUNDO HOJE
        ranking_geral.sort(key=lambda x: x['prio'], reverse=True)
        selecoes_finais = ranking_geral[:12]

        jogos_agrupados = {}
        for s in selecoes_finais:
            m_id = s['id']
            if m_id not in jogos_agrupados:
                jogos_agrupados[m_id] = {"info": s['info'], "liga": s['liga'], "mercados": [], "link": s['link']}
            if len(jogos_agrupados[m_id]["mercados"]) < 3:
                jogos_agrupados[m_id]["mercados"].append(s['mkt'])

        msg = f"🎫 *BILHETE DE ELITE - TOP APOSTAS ({hoje})*\n🎯 12 Melhores Entradas do Mundo\n\n"
        for i, jogo in enumerate(sorted(jogos_agrupados.values(), key=lambda x: x['liga']), 1):
            tipo = "🔥 *Criar Aposta*" if len(jogo['mercados']) > 1 else "🎯 *Aposta Simples*"
            msg += f"{i}. {jogo['info']} | {jogo['liga']}\n{tipo}\n" + "\n".join(jogo['mercados']) + f"\n📊 [Estatísticas]({jogo['link']})\n\n"
        
        msg += "---\nAPOSTAR: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar()
                        
