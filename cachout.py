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

# --- NOVA FUNÇÃO DE CÁLCULO DE GOLS ---
def get_over_stats(team_id):
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
    except:
        return 0

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    # Adicionados IDs 1 e 10 (Copa e Amistosos) conforme seu pedido
    ligas_ids = [
        1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 
        140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637
    ]
    
    horarios_agrupados = {}

    print(f"🔎 Robô CashOut buscando e analisando gols para {hoje}...")

    for l_id in ligas_ids:
        for ano in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if fixtures:
                    for f in fixtures:
                        if f['fixture']['status']['short'] == "NS":
                            t1_id = f['teams']['home']['id']
                            t2_id = f['teams']['away']['id']
                            
                            # Analisa estatística de gols para ordenar
                            perc_t1 = get_over_stats(t1_id)
                            perc_t2 = get_over_stats(t2_id)
                            media_gols = (perc_t1 + perc_t2) / 2

                            # Regra Luciano: Se a casa tem 85% individual, essa é a confiança principal
                            confianca_final = max(perc_t1 if perc_t1 >= 85 else 0, media_gols)

                            data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                            hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                            
                            jogo_info = {
                                "texto": f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']} ({f['league']['name']})",
                                "confianca": confianca_final
                            }
                            
                            if hora_br not in horarios_agrupados:
                                horarios_agrupados[hora_br] = []
                            
                            horarios_agrupados[hora_br].append(jogo_info)
                            time.sleep(0.3) # Proteção para não estourar limite da API
                    break 
            except:
                continue
        time.sleep(0.1)

    # --- ENVIO DOS BILHETES ---
    for hora in sorted(horarios_agrupados.keys()):
        jogos = horarios_agrupados[hora]
        
        if len(jogos) >= 4:
            # ORDENAÇÃO: Coloca os jogos com maior confiança no topo
            jogos.sort(key=lambda x: x['confianca'], reverse=True)

            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos)}\n"
            msg += "📈 *Ordem:* Maior Confiança de Gols\n"
            msg += "----------------------------------\n"
            
            for idx, jogo in enumerate(jogos, 1):
                msg += f"{idx}. {jogo['texto']} - {jogo['confianca']:.0f}%\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            
            enviar_telegram(msg)
            print(f"✅ Bilhete das {hora} enviado!")

if __name__ == "__main__":
    executar_cashout()
    
