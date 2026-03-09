import os
import asyncio
import requests
from datetime import datetime

# --- CONFIGURAÇÃO (GitHub Secrets) --- #
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

def pegar_previsao(fixture_id):
    """ Consulta o endpoint de Predictions para pegar os cálculos prontos """
    url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        if not res.get('response'): return None
        data = res['response'][0]
        
        # Probabilidades calculadas pela API
        perc = data['predictions']['percent']
        
        return {
            "o15": int(perc.get('over_1_5', '0%').replace('%','')),
            "o25": int(perc.get('over_2_5', '0%').replace('%','')),
            "btts": int(perc.get('btts', '0%').replace('%','')),
            "conselho": data['predictions']['advice']
        }
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # LIGAS MAPEADAS (IDs Oficiais)
    ligas_config = {
        39: "Premier League", 140: "LALIGA", 78: "Bundesliga", 135: "Serie A",
        61: "Ligue 1", 94: "Português", 88: "Holandês", 71: "Brasileirão A",
        471: "Paulistão", 472: "Carioca", 141: "LaLiga 2", 62: "Ligue 2",
        203: "Super Lig (Turquia)", 218: "Áustria"
    }
    
    jogos_analisados = []
    ligas_no_bilhete = set()

    print(f"🚀 Iniciando Varredura para o Bilhete do Dia...")

    for l_id, l_nome in ligas_config.items():
        # Testa 2026 (Brasil) e 2025 (Europa)
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            
            if not matches: continue
            
            for m in matches:
                f_id = m['fixture']['id']
                t1, t2 = m['teams']['home']['name'], m['teams']['away']['name']
                hora = m['fixture']['date'][11:16]
                
                print(f"🔮 Analisando: {t1} x {t2}")
                pred = pegar_previsao(f_id)
                
                if pred:
                    mercado = ""
                    prio = 0
                    
                    # --- LÓGICA DE SELEÇÃO IDENTICA AO SEU FRONT ---
                    if pred['o25'] >= 75:
                        mercado = "⚡ +2.5 Gols — Atropelo"
                        prio = 100
                    elif pred['o15'] >= 85:
                        mercado = "⚽ +1.5 Gols — Confiança Máxima"
                        prio = 90
                    elif pred['btts'] >= 75:
                        mercado = "🤝 Ambas Marcam — 4/5 (Est.)"
                        prio = 85
                    elif pred['o15'] >= 70:
                        mercado = "⚽ +1.5 Gols — 4/5 (Est.)"
                        prio = 75
                    elif pred['o15'] >= 50:
                        mercado = "🛡️ +0.5 Gols — Segurança"
                        prio = 60
                    
                    if mercado:
                        ligas_no_bilhete.add(l_nome)
                        jogos_analisados.append({
                            "prio": prio,
                            "liga": l_nome,
                            "texto": f"🏟️ *{t1} x {t2}*\n🕒 {hora} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{f_id})"
                        })
            break 

    if jogos_analisados:
        # Pega os 10 melhores
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        top_10 = jogos_analisados[:10]
        top_10.sort(key=lambda x: x['liga']) # Ordena por liga para o visual

        # --- MONTAGEM DA MENSAGEM (SEU MODELO) ---
        msg = f"🎯 *BILHETE DO DIA ({len(top_10)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for liga in sorted(list(ligas_no_bilhete)):
            msg += f"🔹 {liga}\n"
        
        msg += "\n"
        for i, jogo in enumerate(top_10, 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)
    else:
        print("⚠️ Nenhum jogo qualificado encontrado hoje.")

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
