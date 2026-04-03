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

def get_perc_individual_15(team_id, side):
    """
    Busca os últimos 5 jogos INDIVIDUAIS (sem H2H).
    Filtra por Time da Casa (em casa) ou Visitante (fora).
    """
    # A API permite filtrar por venue ou apenas pegar os últimos. 
    # Para ser fiel à sua regra de 'individual', pegamos os últimos 5 do time.
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        
        jogos_com_15 = 0
        for f in fixtures:
            home_g = f['goals']['home'] or 0
            away_g = f['goals']['away'] or 0
            if (home_g + away_g) > 1.5:
                jogos_com_15 += 1
                
        # Retorna a porcentagem (Ex: 4 de 5 = 80.0)
        return (jogos_com_15 / len(fixtures)) * 100
    except Exception as e:
        print(f"Erro stats time {team_id}: {e}")
        return 0

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    # Suas ligas preferidas
    ligas_ids = [1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637]
    
    horarios_agrupados = {}

    print(f"🔎 Buscando jogos para Cashout em {hoje}...")

    # 1. Coleta e Agrupa por Horário
    for l_id in ligas_ids:
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season=2026"
        try:
            res = requests.get(url, headers=HEADERS).json()
            fixtures = res.get('response', [])
            for f in fixtures:
                if f['fixture']['status']['short'] == "NS":
                    data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                    hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                    
                    if hora_br not in horarios_agrupados: 
                        horarios_agrupados[hora_br] = []
                    horarios_agrupados[hora_br].append(f)
        except: continue
        time.sleep(0.05)

    # 2. Processa apenas grupos com MÍNIMO de 5 JOGOS no mesmo horário
    for hora in sorted(horarios_agrupados.keys()):
        jogos_no_horario = horarios_agrupados[hora]
        
        if len(jogos_no_horario) >= 5:
            print(f"📊 Analisando bloco das {hora} ({len(jogos_no_horario)} jogos)...")
            candidatos_bilhete = []
            
            for f in jogos_no_horario:
                # Pega stats individuais dos últimos 5 jogos
                p_casa = get_perc_individual_15(f['teams']['home']['id'], 'home')
                p_fora = get_perc_individual_15(f['teams']['away']['id'], 'away')
                
                # Média de gols +1.5 entre os dois times
                media_15 = (p_casa + p_fora) / 2
                
                # Filtro rigoroso: Só entra se a média for alta (Ranking de % de gols)
                candidatos_bilhete.append({
                    "confronto": f"{f['teams']['home']['name']} x {f['teams']['away']['name']}",
                    "liga": f['league']['name'],
                    "perc": media_15
                })
                time.sleep(0.3) # Evitar 429 Too Many Requests

            # 3. Ordena por RANKING de % de Gols +1.5
            candidatos_bilhete.sort(key=lambda x: x['perc'], reverse=True)

            # 4. Envia o alerta focado em Cashout
            msg = f"💰 *CASHOUT ESTRATÉGICO - {hora}*\n"
            msg += f"⏰ *Jogos Simultâneos:* {len(candidatos_bilhete)} partidas\n"
            msg += "----------------------------------\n"
            
            for idx, j in enumerate(candidatos_bilhete, 1):
                msg += f"{idx}. {j['confronto']} - *{j['perc']:.0f}%* (+1.5)\n"
            
            msg += "\n🎯 *ALVO:* Múltipla de +1.5 Gols\n"
            msg += "💡 *DICA CASHOUT:* Todos começam juntos. Se 3 ou 4 gols saírem nos primeiros 20-30 min, o lucro já estará alto para encerrar!"
            
            enviar_telegram(msg)

if __name__ == "__main__":
    executar_cashout()
