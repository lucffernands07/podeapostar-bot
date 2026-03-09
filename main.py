import os
import requests
from datetime import datetime

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
        print("✅ Bilhete enviado com sucesso!")
    except:
        print("❌ Erro no Telegram")

def scan_adamchoi_stats(team_id):
    """Analisa histórico real de 10 jogos para todos os mercados"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0, 0
        
        o15, o25, btts, wd, corners = 0, 0, 0, 0, 0
        for f in fixtures:
            g_h, g_a = f['goals']['home'] or 0, f['goals']['away'] or 0
            if (g_h + g_a) >= 2: o15 += 1
            if (g_h + g_a) >= 3: o25 += 1
            if g_h > 0 and g_a > 0: btts += 1
            if (f['teams']['home']['id'] == team_id and g_h >= g_a) or \
               (f['teams']['away']['id'] == team_id and g_a >= g_h): wd += 1
        
        return (o15/10)*100, (o25/10)*100, (btts/10)*100, (wd/10)*100
    except: return 0, 0, 0, 0

def executar():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Iniciando Varredura: {hoje}")
    
    ligas_config = {
        2: "Champions League", 39: "Premier League", 140: "LALIGA", 135: "Serie A",
        78: "Bundesliga", 94: "Português", 71: "Brasileirão A", 239: "Colômbia",
        203: "Süper Lig", 172: "Bulgária", 233: "Egito", 88: "Holandês", 144: "Belga"
    }
    
    jogos_analisados = []
    ligas_encontradas = set()

    for l_id, l_nome in ligas_config.items():
        season = 2026 if l_id in [71, 239] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            for m in matches:
                t1, t2 = m['teams']['home'], m['teams']['away']
                h15, h25, hbtts, hwd = scan_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = scan_adamchoi_stats(t2['id'])
                
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                mercado, nota = "", 0

                # LÓGICA DE SELEÇÃO
                if m25 >= 75: mercado, nota = "⚡ +2.5 Gols — Atropelo", 100
                elif m15 >= 75: mercado, nota = "⚽ +1.5 Gols — 4/5 (Est.)", 90
                elif mbtts >= 75: mercado, nota = "🤝 Ambas Marcam — 4/5 (Est.)", 85
                elif hwd >= 80 or awd >= 80:
                    time_f = t1['name'] if hwd >= awd else t2['name']
                    mercado, nota = f"🛡️ Dupla Chance — {time_f} ou Empate", 75
                elif m15 >= 60: mercado, nota = "🛡️ +0.5 Gols (HT/FT) — Segurança", 70

                if mercado:
                    ligas_encontradas.add(l_nome)
                    # Link AdamChoi corrigido
                    link_stats = f"https://www.adamchoi.co.uk/search?query={t1['name'].replace(' ', '%20')}"
                    
                    canto_txt = "\n🚩 +8.5 Cantos (Tendência)" if m15 > 75 else ""
                    
                    jogos_analisados.append({
                        "prio": nota,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}{canto_txt}\n📊 [Estatísticas]({link_stats})"
                    })
        except: continue

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        
        msg = "🎯 *BILHETE DO DIA (10 JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        msg += "\n".join([f"🔹 {l}" for l in sorted(list(ligas_encontradas))])
        msg += "\n\n"
        
        for i, jogo in enumerate(jogos_analisados[:10], 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar()
            
