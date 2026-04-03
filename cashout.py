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
    except: pass

def get_perc_individual_15(team_id):
    # Pega os últimos 5 jogos individuais (Independente de ser casa ou fora)
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        jogos_com_15 = sum(1 for f in fixtures if (float(f['goals']['home'] or 0) + float(f['goals']['away'] or 0)) > 1.5)
        return (jogos_com_15 / len(fixtures)) * 100
    except: return 0

def executar_cashout():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    
    ligas_ids = [1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637]
    horarios_agrupados = {}

    print(f"🔎 Iniciando captura total para {hoje}...")

    # 1. COLETA SEM FILTROS DE STATUS (Pega tudo das ligas selecionadas)
    for l_id in ligas_ids:
        for season in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if fixtures:
                    for f in fixtures:
                        data_utc = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
                        hora_br = data_utc.astimezone(fuso_br).strftime("%H:%M")
                        
                        if hora_br not in horarios_agrupados:
                            horarios_agrupados[hora_br] = []
                        
                        # Evita duplicidade de ID de partida
                        if f['fixture']['id'] not in [x['fixture']['id'] for x in horarios_agrupados[hora_br]]:
                            horarios_agrupados[hora_br].append(f)
                    break # Encontrou a temporada ativa da liga, pula para a próxima liga
            except: continue
        time.sleep(0.1)

    # 2. PROCESSAMENTO E RANKING POR BLOCO DE HORÁRIO
    for hora in sorted(horarios_agrupados.keys()):
        jogos_do_bloco = horarios_agrupados[hora]
        
        # Só processa se tiver o seu mínimo de 5 jogos simultâneos
        if len(jogos_do_bloco) >= 5:
            print(f"✅ Bloco {hora}: Processando ranking para {len(jogos_do_bloco)} jogos...")
            ranking_final = []
            
            for f in jogos_do_bloco:
                p_home = get_perc_individual_15(f['teams']['home']['id'])
                p_away = get_perc_individual_15(f['teams']['away']['id'])
                media = (p_home + p_away) / 2
                
                ranking_final.append({
                    "confronto": f"{f['teams']['home']['name']} x {f['teams']['away']['name']}",
                    "perc": media
                })
                time.sleep(0.35) # Delay anti-bloqueio

            # ORDENAÇÃO POR % DE GOLS (DO MAIOR PARA O MENOR)
            ranking_final.sort(key=lambda x: x['perc'], reverse=True)

            # 3. MONTAGEM DA MENSAGEM
            msg = f"💰 *CASHOUT {hora}* ({len(ranking_final)} JOGOS)\n"
            msg += "----------------------------------\n"
            for idx, item in enumerate(ranking_final, 1):
                msg += f"{idx}. {item['confronto']} - *{item['perc']:.0f}%*\n"
            
            msg += "\n📈 *Estratégia:* Ranking +1.5 Gols (5 ind.)"
            enviar_telegram(msg)
            print(f"🚀 Mensagem das {hora} enviada com sucesso!")

if __name__ == "__main__":
    executar_cashout()
