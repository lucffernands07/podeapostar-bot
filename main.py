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
        print("✅ Bilhete enviado ao Telegram!", flush=True)
    except: 
        print("❌ Erro ao enviar Telegram", flush=True)

def pegar_previsao(fixture_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        if not res.get('response'): return None
        data = res['response'][0]
        
        p = data.get('predictions', {}).get('percent', {})
        advice = (data.get('predictions', {}).get('advice') or "").lower()
        
        def conv(v):
            if not v: return 0
            return int(str(v).replace('%',''))

        resumo = {
            "o15": conv(p.get('over_1_5')),
            "o25": conv(p.get('over_2_5')),
            "btts": conv(p.get('btts')),
            "home": conv(p.get('home')),
            "draw": conv(p.get('draw')),
            "away": conv(p.get('away')),
            "advice": advice
        }

        # --- MOTOR DE RESGATE (PARA DADOS NULOS) ---
        # Se gols estão zerados, mas o conselho indica algo, a gente "força" a entrada
        if resumo['o15'] == 0:
            if "over 1.5" in advice or "at least 2 goals" in advice:
                resumo['o15'] = 80
            if "over 2.5" in advice or "at least 3 goals" in advice:
                resumo['o25'] = 80
            if "both teams to score" in advice or "btts" in advice:
                resumo['btts'] = 80
        
        # Se vitória está zerada no percent, mas o conselho dá vitória/empate
        if resumo['home'] == 0 or resumo['home'] == 33: # 33% costuma ser o padrão de 'sem cálculo'
            if "win or draw" in advice or "or draw" in advice:
                if "home" in advice or data['predictions']['winner']['name'] in data['teams']['home']['name']:
                    resumo['home'] = 80
                else:
                    resumo['away'] = 80

        print(f"   📊 Final -> O1.5: {resumo['o15']}% | H: {resumo['home']}% | A: {resumo['away']}%", flush=True)
        return resumo
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Iniciando Varredura: {hoje}", flush=True)
    
    # HIERARQUIA: Elite(3000), Nacional(2000), Mata-Mata(1000)
    ligas_config = {
        2: ("Champions", 3000), 39: ("Premier", 3000), 140: ("LALIGA", 3000), 135: ("Serie A", 3000),
        78: ("Bundesliga", 3000), 61: ("Ligue 1", 3000), 94: ("Português", 3000), 71: ("Brasileirão A", 3000),
        203: ("Turquia", 2000), 172: ("Bulgária", 2000), 265: ("Chile", 2000), 239: ("Colômbia", 2000),
        233: ("Egito", 2000), 141: ("LaLiga 2", 2000), 72: ("Brasileirão B", 2000),
        13: ("Liberta", 1000), 11: ("Sula", 1000), 144: ("Copa do Brasil", 1000), 143: ("Copa do Rei", 1000)
    }
    
    jogos_analisados = []
    ligas_encontradas = set()

    for l_id, (l_nome, l_peso) in ligas_config.items():
        season = 2026 if l_id in [71, 72, 13, 11, 265, 239, 144] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            print(f"✅ {l_nome}: {len(matches)} jogos.", flush=True)
            for m in matches:
                t1, t2 = m['teams']['home']['name'], m['teams']['away']['name']
                print(f"🔍 Analisando: {t1} x {t2}", flush=True)
                p = pegar_previsao(m['fixture']['id'])
                if p:
                    mercado, nota = "", 0
                    # PRIORIDADE 1: GOLS (+2.5 -> +1.5 -> +0.5)
                    if p['o25'] >= 75: 
                        mercado, nota = "⚡ +2.5 Gols — Atropelo", 100
                    elif p['o15'] >= 75 or (60 <= p['o25'] <= 74):
                        mercado, nota = f"⚽ +1.5 Gols — {'Confiança Máxima' if p['o15'] >= 75 else '4/5 (Est.)'}", 95
                    elif 60 <= p['o15'] <= 74:
                        mercado, nota = "🛡️ +0.5 Gols — Segurança", 80
                    # PRIORIDADE 2: BTTS
                    elif p['btts'] >= 75:
                        mercado, nota = "🤝 Ambas Marcam — Alta Prob.", 85
                    # PRIORIDADE 3: DUPLA CHANCE (O que salvaria a Lazio hoje)
                    elif p['home'] >= 75 or p['away'] >= 75:
                        time_f = t1 if p['home'] >= p['away'] else t2
                        mercado, nota = f"🛡️ Dupla Chance — {time_f} ou Empate", 70

                    if mercado:
                        ligas_encontradas.add(l_nome)
                        jogos_analisados.append({
                            "prio": l_peso + nota,
                            "texto": f"🏟️ *{t1} x {t2}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{m['fixture']['id']})"
                        })
        except: continue

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = jogos_analisados[:10]
        msg = "🎯 *BILHETE DO DIA — TOP 10*\n💰🍀 *BOA SORTE!*\n\n🏟️ *LIGAS NO BILHETE:*\n"
        msg += " ".join([f"🔹 {l}" for l in sorted(list(ligas_encontradas))]) + "\n\n---\n\n"
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        msg += "---\n💸 *APOSTAR EM:* [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)
    else: print("⚠️ Nenhum jogo qualificado hoje.", flush=True)

if __name__ == "__main__":
    asyncio.run(executar_robo())
            
