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

def get_over_stats_cashout(team_id):
    """Busca estatística de +1.5 para o ranking"""
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
    
    # Lista de Ligas (IDs 1 e 10 inclusos)
    ligas_ids = [
        1, 10, 2, 3, 39, 40, 41, 42, 45, 48, 61, 62, 71, 72, 78, 79, 88, 94, 135, 136, 
        140, 141, 144, 172, 203, 233, 239, 265, 13, 11, 848, 637
    ]
    
    horarios_brutos = {}

    print(f"1️⃣ Agrupando todos os jogos por horário...")

    # PASSO 1: Agrupar tudo o que existe
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
                            
                            if hora_br not in horarios_brutos:
                                horarios_brutos[hora_br] = []
                            
                            horarios_brutos[hora_br].append(f)
                    break 
            except: continue
        time.sleep(0.1)

    # PASSO 2: Filtrar horários com no mínimo 5 jogos e calcular Ranking
    for hora in sorted(horarios_brutos.keys()):
        lista_jogos_hora = horarios_brutos[hora]
        
        if len(lista_jogos_hora) >= 5:
            print(f"2️⃣ Processando ranking para o horário {hora} ({len(lista_jogos_hora)} jogos)...")
            jogos_com_ranking = []

            for f in lista_jogos_hora:
                t1_id = f['teams']['home']['id']
                t2_id = f['teams']['away']['id']
                
                # Busca % para o ranking
                p1 = get_over_stats_cashout(t1_id)
                p2 = get_over_stats_cashout(t2_id)
                
                # Sua Regra: Prioridade 85% casa ou média
                conf = max(p1 if p1 >= 85 else 0, (p1 + p2) / 2)

                jogos_com_ranking.append({
                    "texto": f"🏟️ {f['teams']['home']['name']} x {f['teams']['away']['name']} ({f['league']['name']})",
                    "conf": conf
                })
                time.sleep(0.3) # Delay para API não bloquear

            # PASSO 3: Ordenar o ranking do maior para o menor
            jogos_com_ranking.sort(key=lambda x: x['conf'], reverse=True)

            # PASSO 4: Enviar o bilhete pronto
            msg = f"💰 *CASHOUT: OPORTUNIDADE {hora}*\n"
            msg += f"⏰ *Início simultâneo:* {hora}\n"
            msg += f"📊 *Total de jogos:* {len(jogos_com_ranking)}\n"
            msg += "🏆 *Ranking por Confiança (+1.5):*\n"
            msg += "----------------------------------\n"
            
            for idx, j in enumerate(jogos_com_ranking, 1):
                msg += f"{idx}. {j['texto']} - {j['conf']:.0f}%\n"
            
            msg += "\n✅ *Sugestão:* Múltipla +1.5 Gols\n"
            msg += "📈 *Estratégia:* Encerrar se 70% dos gols saírem cedo!"
            
            enviar_telegram(msg)
            print(f"✅ Bilhete das {hora} enviado com sucesso!")

if __name__ == "__main__":
    executar_cashout()
