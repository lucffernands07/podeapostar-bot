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
        print("✅ Bilhete enviado ao Telegram!")
    except:
        print("❌ Erro no Telegram")

def get_adamchoi_stats(team_id):
    """Calcula a força real baseada nos últimos 10 jogos"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0
        
        o15, o25, btts, wd = 0, 0, 0, 0
        for f in fixtures:
            g_h = f['goals']['home'] if f['goals']['home'] is not None else 0
            g_a = f['goals']['away'] if f['goals']['away'] is not None else 0
            
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
        39: ("Premier League", "premier-league"),
        40: ("Championship", "championship"),
        140: ("LALIGA", "la-liga"),
        141: ("LaLiga 2", "segunda-division"),
        135: ("Serie A", "serie-a"),
        78: ("Bundesliga", "bundesliga"),
        94: ("Português", "primeira-liga"),
        71: ("Brasileirão A", "brazilian-serie-a"),
        239: ("Colômbia", "colombian-primera-a"),
        268: ("Argentina", "argentinian-primera-division"),
        88: ("Holandês", "eredivisie"),
        203: ("Turquia", "turkish-super-lig"),
        262: ("México", "mexican-liga-mx"),
        475: ("Carioca", "brazilian-carioca-a"),
        477: ("Paulista", "brazilian-paulista-a")
    }
    
    todos_jogos_candidatos = []
    ligas_ativas = set()

    print(f"🚀 Iniciando Scanner Global para {hoje}...")

    for l_id, (l_nome, l_slug) in ligas_config.items():
        season = 2026 if l_id in [71, 239, 268, 262, 475, 477] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            for m in matches:
                hora_jogo_br = datetime.fromisoformat(m['fixture']['date'][:-6]) - timedelta(hours=3)
                if hora_jogo_br < agora_br: continue # Pula jogos que já passaram

                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                opcoes = []
                prio_total = 0
                
                # REGRAS E PONTUAÇÃO (PRIORIDADE)
                if hwd >= 80: 
                    opcoes.append(f"🔸 1X ({t1['name']} ou Empate)")
                    prio_total += 40
                elif awd >= 80: 
                    opcoes.append(f"🔸 X2 ({t2['name']} ou Empate)")
                    prio_total += 40
                
                if m25 >= 75: 
                    opcoes.append("🔸 Mais de 2.5 Gols")
                    prio_total += 50
                elif m15 >= 80: 
                    opcoes.append("🔸 Mais de 1.5 Gols")
                    prio_total += 30
                
                # Regra Ambas Marcam (Mínimo 80% conforme sua regra salva)
                if mbtts >= 80: 
                    opcoes.append("🔸 Ambas Marcam — Sim")
                    prio_total += 45
                
                if m15 >= 85:
                    opcoes.append("🔸 +8.5 Cantos (Tendência)")
                    prio_total += 20

                if opcoes:
                    ligas_ativas.add(l_nome)
                    link = f"https://www.adamchoi.co.uk/{l_slug}"
                    titulo = "🔥 *Criar Aposta*" if len(opcoes) >= 2 else "🎯 *Aposta Simples*"
                    
                    todos_jogos_candidatos.append({
                        "prio": prio_total,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora_jogo_br.strftime('%H:%M')} | {l_nome}\n{titulo}\n" + "\n".join(opcoes) + f"\n📊 [Estatísticas]({link})"
                    })
        except: continue

    # SEPARA OS 10 MELHORES POR PONTUAÇÃO
    if todos_jogos_candidatos:
        todos_jogos_candidatos.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = todos_jogos_candidatos[:10]
        
        # Filtra as ligas que realmente entraram no Top 10 para o cabeçalho
        ligas_no_top = set()
        for j in top_10:
            for l_n, l_s in ligas_config.values():
                if l_n in j['texto']: ligas_no_top.add(l_n)

        msg = f"🎯 *TOP 10 BILHETES DO DIA ({hoje})*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n" + "\n".join([f"🔹 {l}" for l in sorted(list(ligas_no_top))]) + "\n\n"
        
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar()
