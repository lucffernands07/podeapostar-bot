import os
import asyncio
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
    try: requests.post(url, json=payload, timeout=15)
    except: print("❌ Erro Telegram")

def pegar_previsao(fixture_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        if not res.get('response'): return None
        data = res['response'][0]
        p = data['predictions']['percent']
        return {
            "o05": int(p.get('over_0_5', '0%').replace('%','')),
            "o15": int(p.get('over_1_5', '0%').replace('%','')),
            "o25": int(p.get('over_2_5', '0%').replace('%','')),
            "btts": int(p.get('btts', '0%').replace('%','')),
            "win_home": int(p.get('home', '0%').replace('%','')),
            "win_away": int(p.get('away', '0%').replace('%','')),
            "conselho": data['predictions']['advice']
        }
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # MAPEAMENTO DAS SUAS LIGAS PARA IDs DA API-FOOTBALL
    ligas_config = {
        144: "Copa do Brasil", 
        71: "Brasileirão A", 
        72: "Brasileirão B",
        471: "Paulistão", 
        472: "Carioca", 
        473: "Mineiro", 
        474: "Gauchão",
        13: "Libertadores", 
        11: "Sudamericana", 
        2: "Champions",
        39: "Premier League", 
        140: "LALIGA", 
        61: "Ligue 1", 
        78: "Bundesliga", 
        135: "Serie A", 
        88: "Holandês", 
        94: "Português", 
        144: "Belga", 
        172: "Búlgaro"
    }
    
    jogos_analisados = []
    ligas_no_bilhete = set()

    for l_id, l_nome in ligas_config.items():
        # Temporada 2026 para Brasil/América e 2025 para Europa
        seasons = [2026] if l_id in [71, 72, 471, 472, 473, 474, 13, 11] else [2025]
        for season in seasons:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            for m in matches:
                f_id = m['fixture']['id']
                t1, t2 = m['teams']['home']['name'], m['teams']['away']['name']
                p = pegar_previsao(f_id)
                
                if p:
                    mercado, prio = "", 0
                    
                    # --- HIERARQUIA DE REGRAS SOLICITADA ---
                    if p['o25'] >= 75:
                        mercado, prio = "⚡ +2.5 Gols — Atropelo", 100
                    elif p['o15'] >= 75 or (60 <= p['o25'] <= 74):
                        mercado, prio = "⚽ +1.5 Gols — Confiança Máxima", 90
                    elif 60 <= p['o15'] <= 74:
                        mercado, prio = "🛡️ +0.5 Gols — Segurança", 80
                    elif p['btts'] >= 75:
                        mercado, prio = "🤝 Ambas Marcam — 4/5 (Est.)", 85
                    elif p['win_home'] >= 75 or p['win_away'] >= 75:
                        time = t1 if p['win_home'] >= 75 else t2
                        mercado, prio = f"🛡️ Dupla Chance — {time} ou Empate", 75
                    elif "corners" in (p['conselho'] or "").lower():
                        mercado, prio = "🚩 +8.5 Escanteios — Volume Alto", 70
                    
                    if mercado:
                        ligas_no_bilhete.add(l_nome)
                        jogos_analisados.append({
                            "prio": prio, "liga": l_nome,
                            "texto": f"🏟️ *{t1} x {t2}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{f_id})"
                        })
            break 

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = jogos_analisados[:10]
        top_10.sort(key=lambda x: x['liga'])

        msg = f"🎯 *BILHETE DO DIA ({len(top_10)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for l in sorted(list(ligas_no_bilhete)): msg += f"🔹 {l}\n"
        msg += "\n"
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
