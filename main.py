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
    if not h2h_data or len(h2h_data) < 2: return None
    total = len(h2h_data)
    o05, o15, o25, btts = 0, 0, 0, 0
    for game in h2h_data:
        g = game['goals']
        soma = (g['home'] or 0) + (g['away'] or 0)
        if soma >= 1: o05 += 1
        if soma >= 2: o15 += 1
        if soma >= 3: o25 += 1
        if (g['home'] or 0) > 0 and (g['away'] or 0) > 0: btts += 1
    return {
        "o05": (o05/total)*100, 
        "o15": (o15/total)*100, 
        "o25": (o25/total)*100, 
        "btts": (btts/total)*100
    }

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    ano = datetime.now().year
    
    # LISTA DE LIGAS COMPLETA (IDs API-FOOTBALL)
    ligas_config = {
        39: "Premier League", 140: "LALIGA", 141: "LaLiga 2", 78: "Bundesliga", 
        135: "Serie A", 61: "Ligue 1", 62: "Ligue 2", 94: "Português", 
        88: "Holandês", 40: "Championship", 71: "Brasileirão A", 
        471: "Paulistão", 472: "Carioca", 144: "Copa do Brasil"
    }
    
    jogos_analisados = []
    ligas_no_bilhete = set()

    print(f"🚀 Iniciando busca de 10 jogos para o bilhete...")

    for l_id, l_nome in ligas_config.items():
        # Tenta temporada atual e anterior para garantir dados
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS, timeout=10).json()
                matches = res.get('response', [])
                if not matches: continue
                
                for item in matches:
                    t1, t2 = item['teams']['home'], item['teams']['away']
                    f_id = item['fixture']['id']
                    
                    url_h2h = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1['id']}-{t2['id']}"
                    h2h_res = requests.get(url_h2h, headers=HEADERS, timeout=10).json()
                    stats = analisar_estatisticas(h2h_res.get('response', [])[:10])

                    if stats:
                        mercado = ""
                        # HIERARQUIA DE ESCOLHA DE MERCADO (O QUE FOR MAIS FORTE)
                        if stats['o25'] >= 75:
                            mercado = "⚡ +2.5 Gols — Atropelo"
                        elif stats['o15'] >= 85:
                            mercado = "⚽ +1.5 Gols — Confiança Máxima"
                        elif stats['btts'] >= 75:
                            mercado = "🤝 Ambas Marcam — 4/5 (Est.)"
                        elif stats['o15'] >= 70:
                            mercado = "⚽ +1.5 Gols — 4/5 (Est.)"
                        elif stats['o05'] >= 90:
                            mercado = "🛡️ +0.5 Gols — Segurança"
                        elif stats['o15'] >= 80:
                            mercado = "🚩 Mais de 8.5 Escanteios — Volume Alto"

                        if mercado:
                            ligas_no_bilhete.add(l_nome)
                            jogos_analisados.append({
                                "forca": max(stats.values()),
                                "liga": l_nome,
                                "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {item['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{f_id})"
                            })
                break 
            except: continue

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['forca'], reverse=True)
        final = jogos_analisados[:10]
        final.sort(key=lambda x: x['liga']) # Organiza por liga no visual
        
        # MONTAGEM DA MENSAGEM (O TEU FRONT)
        mensagem = f"🎯 *BILHETE DO DIA ({len(final)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        
        mensagem += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for liga in sorted(list(ligas_no_bilhete)):
            mensagem += f"🔹 {liga}\n"
        
        mensagem += "\n"
        for i, jogo in enumerate(final, 1):
            mensagem += f"{i}. {jogo['texto']}\n\n"
        
        mensagem += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        
        enviar_telegram(mensagem)
    else:
        print("⚠️ Nenhum jogo aprovado hoje.")

if __name__ == "__main__":
    asyncio.run(executar_robo())
                        
