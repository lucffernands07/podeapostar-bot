import os
import asyncio
import requests
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HOST = "api-football-v1.p.rapidapi.com"

HEADERS = {'x-rapidapi-host': HOST, 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
    except: print("❌ Erro Telegram")

def analisar_estatisticas(h2h_data):
    if not h2h_data or len(h2h_data) < 3: return None # Mínimo de 3 jogos no histórico
    total = len(h2h_data)
    o15, o25, btts = 0, 0, 0
    for game in h2h_data:
        g = game['goals']
        soma = (g['home'] or 0) + (g['away'] or 0)
        if soma >= 2: o15 += 1
        if soma >= 3: o25 += 1
        if (g['home'] or 0) > 0 and (g['away'] or 0) > 0: btts += 1
    return {"o15": (o15/total)*100, "o25": (o25/total)*100, "btts": (btts/total)*100}

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    ano = datetime.now().year
    
    # LIGAS AMPLIADAS PARA GARANTIR 10 JOGOS
    ligas_config = {
        39: ("Premier League", 2025), 140: ("LALIGA", 2025), 141: ("LaLiga 2", 2025),
        78: ("Bundesliga", 2025), 135: ("Serie A", 2025), 61: ("Ligue 1", 2025), 
        62: ("Ligue 2", 2025), 94: ("Português", 2025), 88: ("Holandês", 2025), 
        40: ("Championship", 2025), 71: ("Brasileirão A", 2026), 471: ("Paulistão", 2026)
    }
    
    jogos_selecionados = []
    print(f"🚀 Varrendo ligas para buscar 10 jogos...")

    for l_id, (l_nome, season) in ligas_config.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            for item in res.get('response', []):
                t1, t2 = item['teams']['home'], item['teams']['away']
                
                url_h2h = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1['id']}-{t2['id']}"
                h2h_res = requests.get(url_h2h, headers=HEADERS, timeout=10).json()
                stats = analisar_estatisticas(h2h_res.get('response', [])[:10])

                if stats:
                    # FILTRO MAIS FLEXÍVEL PARA ENCHER O BILHETE
                    if stats['o15'] >= 75:
                        mercado = "⚽ +1.5 Gols — Confiança"
                    elif stats['o15'] >= 50:
                        mercado = "🛡️ +0.5 Gols — Segurança"
                    else: continue

                    extras = []
                    if stats['o25'] >= 65: extras.append("⚡+2.5")
                    if stats['btts'] >= 65: extras.append("🤝BTTS")
                    if stats['o15'] >= 80: extras.append("🚩Cantos")
                    
                    detalhes = f"\n💡 *Dica:* {' | '.join(extras)}" if extras else ""
                    
                    jogos_selecionados.append({
                        "forca": stats['o15'],
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {item['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}{detalhes}"
                    })
        except: continue

    if jogos_selecionados:
        jogos_selecionados.sort(key=lambda x: x['forca'], reverse=True)
        final = jogos_selecionados[:10]
        msg = f"🎯 *BILHETE DO DIA ({len(final)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        for i, jogo in enumerate(final, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        msg += "---\n🤖 *Análise: Gols e Tendências*"
        enviar_telegram(msg)
    else:
        print("⚠️ Poucos jogos no radar hoje.")

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
