import os
import requests
import time
import pytz
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
# IMPORTANTE: Coloque sua nova chave do painel API-SPORTS no GitHub Secrets
API_KEY = os.getenv('X_RAPIDAPI_KEY') 

# MUDANÇA AQUI: Novo Host e cabeçalho para API-SPORTS
HEADERS = {
    'x-apisports-key': API_KEY
}
BASE_URL = "https://v3.football.api-sports.io"

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
    except: pass

def get_over_stats_5(team_id, over_val):
    # Endpoint atualizado
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    try:
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
    
    print(f"--- INICIANDO VALIDAÇÃO (API-SPORTS) ---")
    print(f"🕒 Agora: {agora_br.strftime('%H:%M')} | Janela até: {limite_3h.strftime('%H:%M')}")

    # Ligas baseadas nos seus prints (LaLiga, Serie A, Bundesliga, Ligue 1, etc.)
    ligas = [140, 141, 135, 136, 78, 79, 61, 62, 39, 40, 94, 71, 72, 88, 144, 203, 172, 265, 239, 233, 13, 11]
    jogos_na_janela = []

    for l_id in ligas:
        # Focando nas temporadas 2025 e 2026 conforme solicitado
        for ano in [2025, 2026]:
            url = f"{BASE_URL}/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                response = requests.get(url, headers=HEADERS)
                
                # Log de Quota (O plano free tem 100/dia, bom monitorar)
                if response.status_code == 429:
                    print("⚠️ Limite de requisições atingido. Pausando...")
                    time.sleep(30)
                    continue

                res = response.json()
                fixtures = res.get('response', [])
                if not fixtures: continue
                
                print(f"✅ Liga {l_id} ({ano}): {len(fixtures)} jogos no dia.")
                
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
                
                # Pausa para respeitar o limite de 10 requisições por minuto
                time.sleep(6.1) 
                break 
            except: continue

    if not jogos_na_janela:
        print("ℹ️ Nenhum jogo pendente para as próximas 3h.")
        return

    # Filtro e análise dos Top 10
    jogos_na_janela.sort(key=lambda x: x['hora_obj'])
    top_selecao = jogos_na_janela[:15] # Reduzi para 15 para economizar sua cota de 100/dia

    pool_gols = []
    print(f"📊 Analisando estatísticas para {len(top_selecao)} jogos...")

    for j in top_selecao:
        o15_t1 = get_over_stats_5(j['t1']['id'], 1.5)
        time.sleep(6.1) # Pausa obrigatória entre chamadas
        o15_t2 = get_over_stats_5(j['t2']['id'], 1.5)
        time.sleep(6.1)
        
        probabilidade = (o15_t1 + o15_t2) / 2
        pool_gols.append({
            "info": f"*{j['t1']['name']} x {j['t2']['name']}*",
            "hora": j['hora_str'],
            "liga": j['liga'],
            "perc": probabilidade
        })

    pool_gols.sort(key=lambda x: x['perc'], reverse=True)
    top_10 = pool_gols[:10]

    if not top_10: return

    msg = f"💰 *CASHOUT 3H - TOP 10 GOLS*\n"
    msg += f"⏰ Janela: {agora_br.strftime('%H:%M')} até {limite_3h.strftime('%H:%M')}\n"
    msg += f"----------------------------------\n\n"

    for i, j in enumerate(top_10, 1):
        msg += f"{i}. 🏟️ {j['info']}\n"
        msg += f"🕒 {j['hora']} | {j['liga']}\n"
        msg += f"⚽ *+1.5 Gols:* ({j['perc']:.0f}%)\n\n"

    msg += "---\n🤖 API-SPORTS Ativa"
    enviar_telegram(msg)
    print("🚀 Bilhete enviado!")

if __name__ == "__main__":
    executar_cashout_3h()
