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

def get_perc_ranking(team_id):
    # O segredo está no status=FT (Full Time), para pegar só jogos que acabaram
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        
        jogos_com_gol = 0
        total_jogos_validos = 0
        
        for f in fixtures:
            # Garante que o placar não é Nulo
            gols_home = f['goals']['home'] if f['goals']['home'] is not None else 0
            gols_away = f['goals']['away'] if f['goals']['away'] is not None else 0
            
            total_gols = gols_home + gols_away
            if total_gols > 1.5:
                jogos_com_gol += 1
            total_jogos_validos += 1
            
        if total_jogos_validos == 0: return 0
        return (jogos_com_gol / total_jogos_validos) * 100
    except Exception as e:
        print(f"Erro ao buscar stats do time {team_id}: {e}")
        return 0

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    ligas_ids = [1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637]
    
    horarios_agrupados = {}

    print(f"🔎 Analisando ranking de gols para {hoje}...")

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
                            horarios_agrupados[hora_br].append(f)
                    break
            except: continue
        time.sleep(0.1)

    for hora in sorted(horarios_agrupados.keys()):
        jogos_brutos = horarios_agrupados[hora]
        
        if len(jogos_brutos) >= 5:
            print(f"📊 Calculando ranking real para as {hora}...")
            jogos_com_ranking = []
            
            for f in jogos_brutos:
                p1 = get_perc_ranking(f['teams']['home']['id'])
                p2 = get_perc_ranking(f['teams']['away']['id'])
                
                # Regra Luciano: 85% Casa ou Média
                conf = max(p1 if p1 >= 85 else 0, (p1 + p2) / 2)
                
                info = f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']} ({f['league']['name']})"
                jogos_com_ranking.append({"texto": info, "perc": conf})
                # Pequeno delay para a API não dar erro 429
                time.sleep(0.35)

            # Ordena pelo ranking de confiança
            jogos_com_ranking.sort(key=lambda x: x['perc'], reverse=True)

            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos_com_ranking)}\n"
            msg += "----------------------------------\n"
            for idx, j in enumerate(jogos_com_ranking, 1):
                msg += f"{idx}. {j['texto']} - {j['perc']:.0f}%\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            enviar_telegram(msg)

if __name__ == "__main__":
    executar_cashout()
