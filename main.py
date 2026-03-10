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
        print("✅ Bilhete agrupado enviado!")
    except:
        print("❌ Erro no Telegram")

def get_adamchoi_stats(team_id):
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
    
    ligas_config = {
        2: ("Champions", "uefa-champions-league"),
        39: ("Premier League", "england-premier-league"),
        40: ("Championship", "england-championship"),
        140: ("LALIGA", "spain-la-liga"),
        135: ("Serie A", "italy-serie-a"),
        78: ("Bundesliga", "germany-bundesliga"),
        71: ("Brasileirão A", "brazil-serie-a"),
        239: ("Colômbia", "colombia-colombia-primera-a"),
        268: ("Argentina", "argentina-primera-division"),
        88: ("Holandês", "netherlands-eredivisie")
    }
    
    todas_selecoes_ranking = []

    for l_id, (l_nome, l_slug) in ligas_config.items():
        season = 2026 if l_id in [71, 239, 268] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            for m in res.get('response', []):
                hora_br = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
                if hora_br < agora_br: continue

                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                match_id = m['fixture']['id']
                match_info = f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora_br.strftime('%H:%M')} | {l_nome}"
                link = f"https://www.adamchoi.co.uk/leagues/{l_slug}"

                # Cria as opções individuais para ranqueamento
                if hwd >= 80: todas_selecoes_ranking.append({"prio": hwd, "mkt": f"🔸 1X ({t1['name']} ou Empate)", "id": match_id, "info": match_info, "link": link})
                elif awd >= 80: todas_selecoes_ranking.append({"prio": awd, "mkt": f"🔸 X2 ({t2['name']} ou Empate)", "id": match_id, "info": match_info, "link": link})
                
                if m25 >= 85: todas_selecoes_ranking.append({"prio": m25+5, "mkt": "🔸 Mais de 2.5 Gols", "id": match_id, "info": match_info, "link": link})
                elif m15 >= 80: todas_selecoes_ranking.append({"prio": m15, "mkt": "🔸 Mais de 1.5 Gols", "id": match_id, "info": match_info, "link": link})
                
                if mbtts >= 80: todas_selecoes_ranking.append({"prio": mbtts+2, "mkt": "🔸 Ambas Marcam — Sim", "id": match_id, "info": match_info, "link": link})
                if m15 >= 85: todas_selecoes_ranking.append({"prio": 15, "mkt": "🔸 +8.5 Cantos (Tendência)", "id": match_id, "info": match_info, "link": link})
        except: continue

    if todas_selecoes_ranking:
        # Pega as 10 melhores seleções absolutas do dia
        todas_selecoes_ranking.sort(key=lambda x: x['prio'], reverse=True)
        top_selecoes = todas_selecoes_ranking[:10]

        # AGRUPAMENTO POR JOGO
        bilhete_final = {}
        for sel in top_selecoes:
            m_id = sel['id']
            if m_id not in bilhete_final:
                bilhete_final[m_id] = {"info": sel['info'], "mercados": [], "link": sel['link']}
            
            # Limite de 3 seleções por jogo (conforme sua regra)
            if len(bilhete_final[m_id]["mercados"]) < 3:
                bilhete_final[m_id]["mercados"].append(sel['mkt'])

        msg = f"🔥 *BILHETE DE ELITE - TOP SELEÇÕES ({hoje})*\n🎯 Foco: 8 a 10 Melhores Entradas Agrupadas\n\n"
        
        for i, (m_id, dados) in enumerate(bilhete_final.items(), 1):
            tipo = "🔥 *Criar Aposta*" if len(dados['mercados']) > 1 else "🎯 *Aposta Simples*"
            msg += f"{i}. {dados['info']}\n{tipo}\n" + "\n".join(dados['mercados']) + f"\n📊 [Estatísticas]({dados['link']})\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar()
                
