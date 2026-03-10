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
            g_h = f['goals']['home'] or 0
            g_a = f['goals']['away'] or 0
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
        239: ("Colômbia", "colombia-primera-a"),
        268: ("Argentina", "argentina-primera-division"),
        88: ("Holandês", "netherlands-eredivisie")
    }
    
    todas_selecoes = []

    for l_id, (l_nome, l_slug) in ligas_config.items():
        season = 2026 if l_id in [71, 239, 268] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            for m in matches:
                hora_jogo_br = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
                if hora_jogo_br < agora_br: continue

                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                link = f"https://www.adamchoi.co.uk/leagues/{l_slug}"
                base_txt = f"🏟️ *{t1['name']} x {t2['name']}* ({l_nome})"

                # AVALIAÇÃO INDIVIDUAL DE CADA SELEÇÃO
                # 1. Chance Dupla (80%)
                if hwd >= 80:
                    todas_selecoes.append({"prio": hwd, "texto": f"{base_txt}\n🔸 1X ({t1['name']} ou Empate)", "link": link})
                elif awd >= 80:
                    todas_selecoes.append({"prio": awd, "texto": f"{base_txt}\n🔸 X2 ({t2['name']} ou Empate)", "link": link})
                
                # 2. Mais de 2.5 Gols (RIGOROSO: 85%)
                if m25 >= 85:
                    todas_selecoes.append({"prio": m25 + 5, "texto": f"{base_txt}\n🔸 Mais de 2.5 Gols", "link": link})
                
                # 3. Mais de 1.5 Gols (80%)
                elif m15 >= 80:
                    todas_selecoes.append({"prio": m15, "texto": f"{base_txt}\n🔸 Mais de 1.5 Gols", "link": link})

                # 4. Ambas Marcam (80%)
                if mbtts >= 80:
                    todas_selecoes.append({"prio": mbtts + 2, "texto": f"{base_txt}\n🔸 Ambas Marcam — Sim", "link": link})

        except: continue

    if todas_selecoes:
        # Ordena pela força da estatística e pega as 10 melhores seleções
        todas_selecoes.sort(key=lambda x: x['prio'], reverse=True)
        selecoes_finais = todas_selecoes[:10]

        msg = f"🔥 *BILHETE DE ELITE - TOP SELEÇÕES ({hoje})*\n🎯 Foco: 8 a 10 Melhores Entradas\n\n"
        
        for i, sel in enumerate(selecoes_finais, 1):
            msg += f"{i}. {sel['texto']}\n📊 [Estatísticas]({sel['link']})\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar()
    
