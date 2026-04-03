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

# Função leve para pegar a % de gols sem travar o código
def pegar_porcentagem_gols(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        count = 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total > 1.5: count += 1
        return (count / len(fixtures)) * 100
    except: return 0

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    # IDs das ligas (Incluindo 1 e 10 que você pediu)
    ligas_ids = [
        1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 
        140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637
    ]
    
    horarios_agrupados = {}

    for l_id in ligas_ids:
        for ano in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if fixtures:
                    for f in fixtures:
                        if f['fixture']['status']['short'] == "NS":
                            data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                            hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                            
                            # Aqui o robô calcula a confiança para poder ordenar depois
                            p1 = pegar_porcentagem_gols(f['teams']['home']['id'])
                            p2 = pegar_porcentagem_gols(f['teams']['away']['id'])
                            # Regra: Prioriza 85% da casa ou a média
                            conf = max(p1 if p1 >= 85 else 0, (p1 + p2) / 2)

                            if hora_br not in horarios_agrupados:
                                horarios_agrupados[hora_br] = []
                            
                            horarios_agrupados[hora_br].append({
                                "info": f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']} ({f['league']['name']})",
                                "conf": conf
                            })
                    break 
            except: continue
        time.sleep(0.1)

    # --- ENVIO DOS BILHETES ORDENADOS ---
    for hora in sorted(horarios_agrupados.keys()):
        jogos = horarios_agrupados[hora]
        
        if len(jogos) >= 4:
            # ORDENAÇÃO POR CONFIANÇA (O segredo do CashOut)
            jogos.sort(key=lambda x: x['conf'], reverse=True)

            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos)}\n"
            msg += "----------------------------------\n"
            
            for idx, j in enumerate(jogos, 1):
                msg += f"{idx}. {j['info']} - {j['conf']:.0f}%\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            
            enviar_telegram(msg)

if __name__ == "__main__":
    executar_cashout()
    
