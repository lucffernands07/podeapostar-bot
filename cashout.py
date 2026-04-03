import os
import requests
import pytz
import time
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def obter_odds(fixture_id):
    """Busca as odds de vitória (1X2) para a partida"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/odds?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS).json()
        odds_data = res.get('response', [])
        if not odds_data: return None, None
        
        # Pega as odds do primeiro bookmaker disponível (geralmente Bet365 ou 1xBet)
        for bookmaker in odds_data[0].get('bookmakers', []):
            for bet in bookmaker.get('bets', []):
                if bet['name'] == "Match Winner":
                    odd_casa = next((float(o['odd']) for o in bet['values'] if o['value'] == 'Home'), None)
                    odd_fora = next((float(o['odd']) for o in bet['values'] if o['value'] == 'Away'), None)
                    return odd_casa, odd_fora
        return None, None
    except: return None, None

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    ligas_ids = [1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637]
    
    jogos_por_horario = {}

    print(f"🔎 Analisando favoritos para {hoje}...")

    for l_id in ligas_ids:
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2026"
        try:
            res = requests.get(url, headers=HEADERS).json()
            for f in res.get('response', []):
                f_id = f['fixture']['id']
                odd_h, odd_a = obter_odds(f_id)
                
                # REGRA: Casa menor que Fora E diferença de no mínimo 3.0
                if odd_h and odd_a and odd_h < odd_a and (odd_a - odd_h) >= 3.0:
                    data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                    hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                    
                    if hora_br not in jogos_por_horario:
                        jogos_por_horario[hora_br] = []
                    
                    jogos_por_horario[hora_br].append({
                        "id": f_id,
                        "confronto": f"{f['teams']['home']['name']} x {f['teams']['away']['name']}",
                        "odd_casa": odd_h,
                        "odd_fora": odd_a,
                        "diff": odd_a - odd_h
                    })
                time.sleep(0.1) # Evitar bloqueio
        except: continue

    # Processar blocos com mínimo de 5 jogos que passaram na regra
    for hora in sorted(jogos_por_horario.keys()):
        lista_jogos = jogos_por_horario[hora]
        
        if len(lista_jogos) >= 5:
            # Ordena pela maior diferença de odds (favoritos mais "esmagadores" primeiro)
            lista_jogos.sort(key=lambda x: x['diff'], reverse=True)

            msg = f"💰 *CASHOUT: FAVORITOS DAS {hora}*\n"
            msg += f"🔥 *Regra:* Diferença de Odds >= 3.0 (Mandante)\n"
            msg += f"📊 *Total no padrão:* {len(lista_jogos)} jogos\n"
            msg += "----------------------------------\n"
            
            for idx, j in enumerate(lista_jogos, 1):
                msg += f"{idx}. {j['confronto']}\n"
                msg += f"   🏠 Odd {j['odd_casa']:.2f} | ✈️ Odd {j['odd_fora']:.2f} (Diff: {j['diff']:.1f})\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Foco:* Favoritismo em casa para Cashout rápido!"
            
            enviar_telegram(msg)
            print(f"🚀 Bilhete das {hora} enviado!")

if __name__ == "__main__":
    executar_cashout()
            
