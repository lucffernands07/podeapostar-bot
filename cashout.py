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
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5"
    try:
        response = requests.get(url, headers=HEADERS)
        # Se bater no limite durante a análise de estatísticas, espera um pouco
        if response.status_code == 429:
            time.sleep(10)
            response = requests.get(url, headers=HEADERS)
            
        if response.status_code != 200: return 0
        res = response.json()
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
    
    print(f"--- INICIANDO VALIDAÇÃO ---")
    print(f"🕒 Agora: {agora_br.strftime('%H:%M')} | Janela até: {limite_3h.strftime('%H:%M')}")
    
    if not API_KEY:
        print("❌ ERRO: X_RAPIDAPI_KEY não configurada.")
        return

    # Ligas baseadas nas fotos enviadas
    ligas = [2, 3, 39, 40, 140, 141, 135, 136, 78, 79, 61, 62, 94, 71, 72, 88, 144, 203, 172, 265, 239, 233, 13, 11]
    jogos_na_janela = []

    for l_id in ligas:
        # Buscamos 2025 primeiro (maioria das ligas das fotos são 25/26)
        for ano in [2025, 2026]:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                response = requests.get(url, headers=HEADERS)
                
                # Trata limite de requisições por minuto (Status 429)
                if response.status_code == 429:
                    print(f"⏳ Limite atingido na Liga {l_id}. Aguardando 15s...")
                    time.sleep(15)
                    response = requests.get(url, headers=HEADERS)

                if response.status_code == 403:
                    print(f"❌ Erro 403: Sem permissão ou cota diária esgotada (Liga {l_id})")
                    continue
                elif response.status_code != 200:
                    print(f"⚠️ Status {response.status_code} na Liga {l_id}")
                    continue

                res = response.json()
                if res.get('errors'):
                    print(f"⚠️ Erro API (Liga {l_id}): {res['errors']}")
                    continue

                fixtures = res.get('response', [])
                if not fixtures: 
                    continue
                
                print(f"✅ Liga {l_id} ({ano}): {len(fixtures)} jogos encontrados.")
                
                for f in fixtures:
                    if f['fixture']['status']['short'] != "NS": continue
                    
                    data_jogo = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br)
                    
                    if agora_br < data_jogo <= limite_3h:
                        jogos_na_janela.append({
                            "id": f['fixture']['id'],
                            "t1": f['teams']['home'],
                            "t2": f['teams']['away'],
                            "hora_obj": data_jogo,
                            "hora_str": data_jogo.strftime("%H:%M"),
                            "liga": f['league']['name']
                        })
                
                # Pausa estratégica para não estourar os 10req/min do plano Free
                time.sleep(2.0)
                break 

            except Exception as e:
                print(f"💥 Erro na Liga {l_id}: {e}")
                continue

    if not jogos_na_janela:
        print("ℹ️ Nenhum jogo 'NS' encontrado para as próximas 3h.")
        return

    # PRIORIDADE: 20 mais cedo
    jogos_na_janela.sort(key=lambda x: x['hora_obj'])
    top_20_cedo = jogos_na_janela[:20]

    # PRIORIDADE: Cálculo de Gols
    pool_gols = []
    print(f"📊 Analisando +1.5 Gols em {len(top_20_cedo)} jogos...")

    for j in top_20_cedo:
        o15_t1 = get_over_stats_5(j['t1']['id'], 1.5)
        time.sleep(1.5) # Pausa entre times
        o15_t2 = get_over_stats_5(j['t2']['id'], 1.5)
        
        probabilidade = (o15_t1 + o15_t2) / 2
        
        pool_gols.append({
            "info": f"*{j['t1']['name']} x {j['t2']['name']}*",
            "hora": j['hora_str'],
            "liga": j['liga'],
            "perc": probabilidade
        })
        time.sleep(1.0) # Pausa entre jogos

    pool_gols.sort(key=lambda x: x['perc'], reverse=True)
    top_10_gols = pool_gols[:10]

    if not top_10_gols: return

    # Mensagem Final
    msg = f"💰 *CASHOUT 3H - TOP 10 GOLS*\n"
    msg += f"⏰ Janela: {agora_br.strftime('%H:%M')} até {limite_3h.strftime('%H:%M')}\n"
    msg += f"----------------------------------\n\n"

    for i, j in enumerate(top_10_gols, 1):
        msg += f"{i}. 🏟️ {j['info']}\n"
        msg += f"🕒 {j['hora']} | {j['liga']}\n"
        msg += f"⚽ *+1.5 Gols:* ({j['perc']:.0f}%)\n\n"

    msg += "---\n💸 [Betano](https://www.betano.com) | [Bet365](https://www.bet365.com)"
    enviar_telegram(msg)
    print("🚀 Bilhete enviado!")

if __name__ == "__main__":
    executar_cashout_3h()
