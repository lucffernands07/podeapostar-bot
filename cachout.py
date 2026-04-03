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

# --- FUNÇÃO DE RANKING (ADICIONADA) ---
def get_perc_ranking(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
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
    
    # Lista expandida (Ligas originais + 1 e 10 da Copa/Amistosos)
    ligas_ids = [
        1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 
        140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637
    ]
    
    horarios_agrupados = {}

    print(f"🔎 Robô CashOut buscando jogos para {hoje}...")

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
                            
                            if hora_br not in horarios_agrupados:
                                horarios_agrupados[hora_br] = []
                            
                            # Agora guardamos o objeto completo para processar o ranking depois
                            horarios_agrupados[hora_br].append(f)
                    break
            except:
                continue
        time.sleep(0.1)

    # --- ENVIO DOS BILHETES ---
    for hora in sorted(horarios_agrupados.keys()):
        jogos_brutos = horarios_agrupados[hora]
        
        # REGRA MESTRA: Mínimo de 5 jogos no mesmo horário (conforme seu pedido)
        if len(jogos_brutos) >= 5:
            print(f"📊 Processando Ranking para o horário {hora}...")
            jogos_com_ranking = []

            for f in jogos_brutos:
                t1_id = f['teams']['home']['id']
                t2_id = f['teams']['away']['id']
                
                # Cálculo da sua regra Luciano (85% casa ou média)
                p1 = get_perc_ranking(t1_id)
                p2 = get_perc_ranking(t2_id)
                conf = max(p1 if p1 >= 85 else 0, (p1 + p2) / 2)

                info_texto = f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']} ({f['league']['name']})"
                jogos_com_ranking.append({"texto": info_texto, "perc": conf})
                time.sleep(0.2) # Proteção API

            # ORDENAÇÃO: Aqui a mágica acontece. Coloca o maior % no topo.
            jogos_com_ranking.sort(key=lambda x: x['perc'], reverse=True)

            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos_com_ranking)}\n"
            msg += "----------------------------------\n"
            
            for idx, jogo in enumerate(jogos_com_ranking, 1):
                msg += f"{idx}. {jogo['texto']} - {jogo['perc']:.0f}%\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            
            enviar_telegram(msg)
            print(f"✅ Bilhete das {hora} enviado!")

if __name__ == "__main__":
    executar_cashout()
