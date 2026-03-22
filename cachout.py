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
    except Exception as e:
        print(f"Erro Telegram: {e}")

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    # Lista expandida para não perder nada no mundo
    ligas_ids = [
        2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 
        140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637
    ]
    
    horarios_agrupados = {}

    print(f"🔎 Robô CashOut buscando jogos para {hoje}...")

    for l_id in ligas_ids:
        # Tenta temporada 2026, se falhar tenta 2025
        for ano in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if fixtures:
                    for f in fixtures:
                        # Apenas jogos que NÃO começaram
                        if f['fixture']['status']['short'] == "NS":
                            data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                            hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                            
                            jogo_info = f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']}"
                            liga_nome = f['league']['name']
                            
                            if hora_br not in horarios_agrupados:
                                horarios_agrupados[hora_br] = []
                            
                            horarios_agrupados[hora_br].append(f"{jogo_info} ({liga_nome})")
                    break # Se achou a temporada certa, pula pro próximo ID de liga
            except:
                continue
        time.sleep(0.2) # Evita spam na API

    # --- ENVIO DOS BILHETES ---
    for hora in sorted(horarios_agrupados.keys()):
        jogos = horarios_agrupados[hora]
        
        # REGRA MESTRA: Mínimo de 4 jogos no mesmo horário
        if len(jogos) >= 4:
            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos)}\n"
            msg += "----------------------------------\n"
            
            for idx, info in enumerate(jogos, 1):
                msg += f"{idx}. {info}\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            
            enviar_telegram(msg)
            print(f"✅ Bilhete das {hora} enviado!")

if __name__ == "__main__":
    executar_cashout()
