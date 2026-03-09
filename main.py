import os
import asyncio
import requests
from datetime import datetime

# --- CONFIGURAÇÃO DE AMBIENTE --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    try: 
        requests.post(url, json=payload, timeout=15)
        print("✅ Bilhete enviado com sucesso!", flush=True)
    except Exception as e: 
        print(f"❌ Erro ao enviar Telegram: {e}", flush=True)

def pegar_previsao(fixture_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        if not res.get('response'): return None
        data = res['response'][0]
        p = data['predictions']['percent']
        
        def conv(v): return int(str(v).replace('%','')) if v else 0

        previsao = {
            "o05": conv(p.get('over_0_5')),
            "o15": conv(p.get('over_1_5')),
            "o25": conv(p.get('over_2_5')),
            "btts": conv(p.get('btts')),
            "win_home": conv(p.get('home')),
            "win_away": conv(p.get('away')),
            "conselho": (data['predictions']['advice'] or "").lower()
        }
        # Log de validação para conferência no GitHub
        print(f"   📊 Stats -> 1.5: {previsao['o15']}% | 2.5: {previsao['o25']}% | BTTS: {previsao['btts']}%", flush=True)
        return previsao
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Iniciando Varredura: {hoje}", flush=True)
    
    # MAPEAMENTO COMPLETO (ID: (Nome, Peso_Hierarquia))
    # Elite = 3000 | Nacional = 2000 | Mata-Mata = 1000
    ligas_config = {
        # --- ELITE ---
        2: ("Champions League", 3000), 39: ("Premier League", 3000), 140: ("LALIGA", 3000), 
        135: ("Serie A", 3000), 78: ("Bundesliga", 3000), 61: ("Ligue 1", 3000), 
        94: ("Português", 3000), 71: ("Brasileirão A", 3000), 88: ("Holandês", 3000), 144: ("Belga", 3000),
        # --- NACIONAIS (SEUS PRINTS) ---
        203: ("Süper Lig", 2000), 172: ("Bulgária", 2000), 265: ("Chile", 2000), 
        239: ("Colômbia", 2000), 233: ("Egito", 2000), 141: ("LaLiga 2", 2000), 72: ("Brasileirão B", 2000),
        # --- MATA-MATA & COPAS ---
        13: ("Libertadores", 1000), 11: ("Sudamericana", 1000), 45: ("FA Cup", 1000),
        143: ("Copa del Rey", 1000), 137: ("Coppa Italia", 1000), 81: ("DFB Pokal", 1000)
    }
    
    jogos_analisados = []
    ligas_encontradas = set()

    for l_id, (l_nome, l_peso) in ligas_config.items():
        season = 2026 if l_id in [71, 72, 13, 11, 265, 239] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            print(f"✅ {l_nome}: {len(matches)} jogos encontrados.", flush=True)
            
            for m in matches:
                f_id = m['fixture']['id']
                t1, t2 = m['teams']['home']['name'], m['teams']['away']['name']
                print(f"🔍 Analisando: {t1} x {t2}", flush=True)
                
                p = pegar_previsao(f_id)
                if p:
                    mercado, nota = "", 0
                    
                    # --- REGRAS DE OURO DO LUCIANO ---
                    # 1. Regra +2.5
                    if p['o25'] >= 75:
                        mercado, nota = "⚡ +2.5 Gols — Atropelo", 100
                    
                    # 2. Regra +1.5 (Rebaixamento do 2.5 ou Confiança no 1.5)
                    elif p['o15'] >= 75 or (60 <= p['o25'] <= 74):
                        status = "Confiança Máxima" if p['o15'] >= 75 else "4/5 (Est.)"
                        mercado, nota = f"⚽ +1.5 Gols — {status}", 90
                    
                    # 3. Regra +0.5 (Rebaixamento do 1.5)
                    elif 60 <= p['o15'] <= 74:
                        mercado, nota = "🛡️ +0.5 Gols — Segurança", 80
                    
                    # 4. BTTS
                    elif p['btts'] >= 75:
                        mercado, nota = "🤝 Ambas Marcam — Alta Prob.", 85
                    
                    # 5. Dupla Chance
                    elif p['win_home'] >= 75 or p['win_away'] >= 75:
                        time = t1 if p['win_home'] >= 75 else t2
                        mercado, nota = f"🛡️ Dupla Chance — {time} ou Empate", 70

                    if mercado:
                        ligas_encontradas.add(l_nome)
                        jogos_analisados.append({
                            "prio": l_peso + nota,
                            "texto": f"🏟️ *{t1} x {t2}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{f_id})"
                        })
        except: continue

    if jogos_analisados:
        # Ordenação por Hierarquia de Liga e depois por força da predição
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = jogos_analisados[:10]
        
        # FRONT-END CAPRICHADO
        msg = "🎯 *BILHETE DO DIA — TOP 10*\n"
        msg += "💰🍀 *BOA SORTE NOS PALPITES!*\n\n"
        
        msg += "🏟️ *LIGAS NO BILHETE:*\n"
        for liga in sorted(list(ligas_encontradas)):
            msg += f"🔹 {liga} "
        msg += "\n\n---\n\n"
        
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        msg += "---\n💸 *APOSTAR EM:* [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        
        enviar_telegram(msg)
    else:
        print("⚠️ Fim da varredura: Nenhum jogo atingiu os critérios mínimos.", flush=True)

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
