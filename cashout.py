import os
import requests
import time
import pytz
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
    except: pass

def get_over_stats_5(team_id, over_val):
    # Estatística de Gols baseada nos últimos 5 jogos (Forma Atual)
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        count = 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total > over_val: count += 1
        return (count / len(fixtures)) * 100
    except: return 0

def executar_cashout_3h():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    limite_3h = agora_br + timedelta(hours=3)
    
    hoje = agora_br.strftime("%Y-%m-%d")
    print(f"🔎 Iniciando Cashout. Agora: {agora_br.strftime('%H:%M')} | Limite: {limite_3h.strftime('%H:%M')}")

    ligas = [2, 39, 140, 135, 78, 61, 94, 71, 88, 144, 203, 172, 265, 239, 233, 141, 72, 13, 11]
    jogos_na_janela = []

    for l_id in ligas:
        for ano in [2026, 2025]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                res = requests.get(url, headers=HEADERS).json()
                fixtures = res.get('response', [])
                if not fixtures: continue
                
                for f in fixtures:
                    if f['fixture']['status']['short'] != "NS": continue
                    
                    data_jogo = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br)
                    
                    # Filtro de tempo: entre AGORA e AGORA + 3 HORAS
                    if agora_br < data_jogo <= limite_3h:
                        jogos_na_janela.append({
                            "id": f['fixture']['id'],
                            "t1": f['teams']['home'],
                            "t2": f['teams']['away'],
                            "hora_obj": data_jogo,
                            "hora_str": data_jogo.strftime("%H:%M"),
                            "liga": f['league']['name']
                        })
                break
            except: continue

    if not jogos_na_janela:
        print("Nenhum jogo encontrado para as próximas 3 horas.")
        return

    # PRIORIDADE 1: Pegar os 20 jogos mais cedo (ordem cronológica)
    jogos_na_janela.sort(key=lambda x: x['hora_obj'])
    top_20_cedo = jogos_na_janela[:20]

    # PRIORIDADE 2: Calcular probabilidade de +1.5 gols e Rankear
    pool_gols = []
    print(f"📊 Analisando +1.5 Gols em {len(top_20_cedo)} jogos...")

    for j in top_20_cedo:
        o15_t1 = get_over_stats_5(j['t1']['id'], 1.5)
        time.sleep(0.3) # Delay API
        o15_t2 = get_over_stats_5(j['t2']['id'], 1.5)
        
        probabilidade = (o15_t1 + o15_t2) / 2
        
        pool_gols.append({
            "info": f"*{j['t1']['name']} x {j['t2']['name']}*",
            "hora": j['hora_str'],
            "liga": j['liga'],
            "perc": probabilidade
        })

    # Ordenar pelos 10 melhores em probabilidade de gols
    pool_gols.sort(key=lambda x: x['perc'], reverse=True)
    top_10_gols = pool_gols[:10]

    if not top_10_gols: return

    # Montagem do Bilhete
    msg = f"💰 *CASHOUT 3H - TOP 10 GOLS*\n"
    msg += f"⏰ Janela: {agora_br.strftime('%H:%M')} até {limite_3h.strftime('%H:%M')}\n"
    msg += f"----------------------------------\n\n"

    for i, j in enumerate(top_10_gols, 1):
        msg += f"{i}. 🏟️ {j['info']}\n"
        msg += f"🕒 {j['hora']} | {j['liga']}\n"
        msg += f"⚽ *+1.5 Gols:* ({j['perc']:.0f}%)\n\n"

    msg += "---\n💸 [Betano](https://www.betano.com) | [Bet365](https://www.bet365.com)"
    enviar_telegram(msg)
    print("🚀 Bilhete de Cashout enviado!")

if __name__ == "__main__":
    executar_cashout_3h()
