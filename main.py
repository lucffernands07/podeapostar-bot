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
        print("✅ Bilhete enviado!")
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
            g_h, g_a = f['goals']['home'] or 0, f['goals']['away'] or 0
            if (g_h + g_a) >= 2: o15 += 1
            if (g_h + g_a) >= 3: o25 += 1
            if g_h > 0 and g_a > 0: btts += 1
            if (f['teams']['home']['id'] == team_id and g_h >= g_a) or \
               (f['teams']['away']['id'] == team_id and g_a >= g_h): wd += 1
        return (o15*10), (o25*10), (btts*10), (wd*10)
    except: return 0, 0, 0, 0

def executar():
    # Ajuste de Data para o fuso de Brasília
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    print(f"🚀 Varredura para o dia: {hoje}")
    
    ligas_config = {
        2: ("Champions", "uefa-champions-league"),
        39: ("Premier League", "premier-league"),
        140: ("LALIGA", "la-liga"),
        135: ("Serie A", "serie-a"),
        78: ("Bundesliga", "bundesliga"),
        94: ("Português", "primeira-liga"),
        71: ("Brasileirão A", "brazilian-serie-a"),
        239: ("Colômbia", "colombian-primera-a"),
        88: ("Holandês", "eredivisie"),
        203: ("Turquia", "turkish-super-lig"),
        475: ("Carioca", "brazilian-carioca-a"),
        477: ("Paulista", "brazilian-paulista-a")
    }
    
    bilhete = []
    ligas_encontradas = set()

    for l_id, (l_nome, l_slug) in ligas_config.items():
        season = 2026 if l_id in [71, 239, 475, 477] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            for m in matches:
                # Verificação extra: Se o jogo já passou do horário atual, ignora
                hora_jogo = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
                if hora_jogo < agora_br: continue

                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                opcoes = []
                prio = 0
                
                if hwd >= 80: 
                    opcoes.append(f"🔸 1X ({t1['name']} ou Empate)")
                    prio += 40
                elif awd >= 80: 
                    opcoes.append(f"🔸 X2 ({t2['name']} ou Empate)")
                    prio += 40
                if m25 >= 75: 
                    opcoes.append("🔸 Mais de 2.5 Gols")
                    prio += 50
                elif m15 >= 75: 
                    opcoes.append("🔸 Mais de 1.5 Gols")
                    prio += 30
                if mbtts >= 75: 
                    opcoes.append("🔸 Ambas Marcam — Sim")
                    prio += 35
                if m15 >= 80:
                    opcoes.append("🔸 +8.5 Cantos (Tendência)")
                    prio += 15

                if opcoes:
                    ligas_encontradas.add(l_nome)
                    link = f"https://www.adamchoi.co.uk/{l_slug}"
                    titulo = "🔥 *Criar Aposta*" if len(opcoes) >= 2 else "🎯 *Aposta Simples*"
                    
                    bilhete.append({
                        "prio": prio,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora_jogo.strftime('%H:%M')} | {l_nome}\n{titulo}\n" + "\n".join(opcoes) + f"\n📊 [Estatísticas]({link})"
                    })
        except: continue

    if bilhete:
        bilhete.sort(key=lambda x: x['prio'], reverse=True)
        msg = f"🎯 *BILHETE DO DIA ({hoje})*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n" + "\n".join([f"🔹 {l}" for l in sorted(list(ligas_encontradas))]) + "\n\n"
        for i, jogo in enumerate(bilhete[:10], 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)
    else:
        print("⚠️ Sem jogos para o horário restante de hoje.")

if __name__ == "__main__":
    executar()
