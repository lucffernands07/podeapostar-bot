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
    try: 
        requests.post(url, json=payload, timeout=15)
        print("✅ Mensagem enviada ao Telegram!", flush=True)
    except Exception as e: 
        print(f"❌ Erro Telegram: {e}", flush=True)

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
    print(f"🚀 Iniciando Varredura: {hoje}", flush=True)
    
    ligas_config = {
        # ELITE (Peso 3)
        2: ("Champions League", 3), 39: ("Premier League", 3), 140: ("LALIGA", 3), 
        135: ("Serie A", 3), 78: ("Bundesliga", 3), 61: ("Ligue 1", 3), 
        94: ("Português", 3), 71: ("Brasileirão A", 3), 88: ("Holandês", 3), 144: ("Belga", 3),
        # NACIONAIS (Peso 2)
        203: ("Süper Lig", 2), 172: ("Bulgária", 2), 265: ("Chile", 2), 
        239: ("Colômbia", 2), 233: ("Egito", 2), 141: ("LaLiga 2", 2), 72: ("Brasileirão B", 2),
        # MATA-MATA (Peso 1)
        13: ("Libertadores", 1), 11: ("Sudamericana", 1), 144: ("Copa do Brasil", 1), 
        45: ("FA Cup", 1), 48: ("League Cup", 1), 143: ("Copa del Rey", 1), 
        137: ("Coppa Italia", 1), 81: ("DFB Pokal", 1), 66: ("Coupe de France", 1)
    }
    
    jogos_analisados = []
    
    for l_id, (l_nome, l_peso) in ligas_config.items():
        seasons = [2026] if l_id in [71, 72, 13, 11, 265, 239, 144] else [2025]
        for season in seasons:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                matches = res.get('response', [])
                if not matches: continue
                
                print(f"📊 {l_nome}: {len(matches)} jogos encontrados.", flush=True)
                
                for m in matches:
                    f_id = m['fixture']['id']
                    t1, t2 = m['teams']['home']['name'], m['teams']['away']['name']
                    p = pegar_previsao(f_id)
                    if p:
                        mercado, prio_mercado = "", 0
                        if p['o25'] >= 75:
                            mercado, prio_mercado = "⚡ +2.5 Gols — Atropelo", 100
                        elif p['o15'] >= 75 or (60 <= p['o25'] <= 74):
                            mercado, prio_mercado = "⚽ +1.5 Gols — Confiança Máxima", 90
                        elif 60 <= p['o15'] <= 74:
                            mercado, prio_mercado = "🛡️ +0.5 Gols — Segurança", 80
                        elif p['btts'] >= 75:
                            mercado, prio_mercado = "🤝 Ambas Marcam", 85
                        elif p['win_home'] >= 75 or p['win_away'] >= 75:
                            time = t1 if p['win_home'] >= 75 else t2
                            mercado, prio_mercado = f"🛡️ Dupla Chance — {time}", 75
                        
                        if mercado:
                            prio_final = prio_mercado + (l_peso * 1000)
                            jogos_analisados.append({
                                "prio": prio_final,
                                "texto": f"🏟️ *{t1} x {t2}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{f_id})"
                            })
            except: continue

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = jogos_analisados[:10]
        
        msg = f"🎯 *BILHETE DO DIA ({len(top_10)} JOGOS)*\n💰 BOA SORTE!\n\n"
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        enviar_telegram(msg)
    else:
        print("⚠️ Nenhum jogo qualificado encontrado para as regras.", flush=True)

if __name__ == "__main__":
    asyncio.run(executar_robo())
    
