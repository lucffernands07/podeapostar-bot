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
    try:
        requests.post(url, json=payload)
    except:
        pass

def obter_odds(fixture_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/odds?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS).json()
        odds_data = res.get('response', [])
        if not odds_data: return None, None
        
        for bookmaker in odds_data[0].get('bookmakers', []):
            for bet in bookmaker.get('bets', []):
                if bet['name'] == "Match Winner":
                    o_h = next((float(o['odd']) for o in bet['values'] if o['value'] == 'Home'), None)
                    o_a = next((float(o['odd']) for o in bet['values'] if o['value'] == 'Away'), None)
                    return o_h, o_a
        return None, None
    except: return None, None

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    ligas_ids = [1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637]
    
    # 1. COLETA BRUTA (Agrupar TUDO por horário primeiro)
    coleta_bruta = {}

    for l_id in ligas_ids:
        # Tenta buscar em 2026 e depois em 2025
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                
                if fixtures:
                    for f in fixtures:
                        # Apenas jogos que não começaram
                        if f['fixture']['status']['short'] == "NS":
                            data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                            hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                            
                            if hora_br not in coleta_bruta:
                                coleta_bruta[hora_br] = []
                            
                            # Evita duplicar o jogo se a API retornar em ambas as temporadas
                            if f['fixture']['id'] not in [x['fixture']['id'] for x in coleta_bruta[hora_br]]:
                                coleta_bruta[hora_br].append(f)
                    
                    # Se encontrou jogos nesta temporada, para de procurar e vai para a próxima liga
                    break 
            except: 
                continue
        time.sleep(0.05)

    # 2. TRAVA DO BILHETE (Verifica se o horário tem volume)
    for hora in sorted(coleta_bruta.keys()):
        total_jogos_janela = coleta_bruta[hora]
        
        if len(total_jogos_janela) >= 5:
            print(f"⏰ Janela das {hora} com {len(total_jogos_janela)} jogos. Aplicando Filtro de Elite...")
            
            # 3. FILTRO DE ELITE (Diferença de Odds dentro da janela aprovada)
            jogos_elite = []
            for f in total_jogos_janela:
                odd_h, odd_a = obter_odds(f['fixture']['id'])
                
                # Regra: Casa < Fora e Diferença >= 3.0
                if odd_h and odd_a and odd_h < odd_a and (odd_a - odd_h) >= 3.0:
                    jogos_elite.append({
                        "confronto": f"{f['teams']['home']['name']} x {f['teams']['away']['name']}",
                        "odd_h": odd_h,
                        "odd_a": odd_a,
                        "diff": odd_a - odd_h
                    })
                time.sleep(0.3) # Delay para não estourar a API

            # Envia o bilhete apenas se o FILTRO DE ELITE encontrou jogos
            if jogos_elite:
                # Ordena pelo maior favoritismo
                jogos_elite.sort(key=lambda x: x['diff'], reverse=True)

                msg = f"💰 *CASHOUT ELITE - {hora}*\n"
                msg += f"🏟️ *Janela:* {len(total_jogos_janela)} jogos\n"
                msg += f"🎯 *No padrão (Diff >= 3.0):* {len(jogos_elite)}\n"
                msg += "----------------------------------\n"
                
                for idx, j in enumerate(jogos_elite, 1):
                    msg += f"{idx}. {j['confronto']} - *Diff: {j['diff']:.1f}*\n"
                
                msg += "\n✅ *Mercado:* +1.5 Gols"
                enviar_telegram(msg)

if __name__ == "__main__":
    executar_cashout()
                
