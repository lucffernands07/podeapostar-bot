import os
import requests
import time
import pytz
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('API_SPORTS_KEY') 

HEADERS = {
    'x-apisports-key': API_KEY
}
BASE_URL = "https://v3.football.api-sports.io"

def log(tag, msg):
    print(f"LOG: [{tag}] {msg}")

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload)
        log("TELEGRAM", "Mensagem enviada com sucesso ao Bot.")
    except Exception as e:
        log("ERRO-TG", f"Falha ao enviar mensagem: {e}")

def get_over_stats_5(team_id, team_name, over_val):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    try:
        log("STATS", f"Analisando últimos 5 jogos de: {team_name}")
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            log("ERRO-API", f"Status {response.status_code} ao buscar stats de {team_name}")
            return 0
            
        res = response.json()
        fixtures = res.get('response', [])
        
        if not fixtures:
            log("AVISO", f"Nenhum histórico encontrado para {team_name}")
            return 0
            
        count = 0
        for f in fixtures:
            total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if total > over_val: count += 1
            
        return (count / len(fixtures)) * 100
    except Exception as e:
        log("ERRO-PROCESS", f"Falha em stats de {team_name}: {e}")
        return 0

def executar_cashout_3h():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    limite_3h = agora_br + timedelta(hours=3)
    hoje = agora_br.strftime("%Y-%m-%d")
    
    log("SISTEMA", "--- INICIANDO CASHOUT 3H ---")
    log("HORÁRIO", f"Agora: {agora_br.strftime('%H:%M')} | Janela até: {limite_3h.strftime('%H:%M')}")

    ligas = [140, 141, 135, 136, 78, 79, 61, 62, 39, 40, 94, 71, 72, 88, 144, 203, 172, 265, 239, 233, 13, 11]
    jogos_na_janela = []

    for l_id in ligas:
        for ano in [2025, 2026]:
            url = f"{BASE_URL}/fixtures?date={hoje}&league={l_id}&season={ano}"
            try:
                log("BUSCA", f"Verificando Liga {l_id} (Temporada {ano})")
                response = requests.get(url, headers=HEADERS)
                
                if response.status_code == 403:
                    log("ERRO-CRÍTICO", "Chave API Inválida ou Plano Expirado (403).")
                    return

                if response.status_code == 429:
                    log("LIMITE", "⚠️ 100 requisições diárias atingidas ou 10/min. Pausando 30s...")
                    time.sleep(30)
                    continue

                res = response.json()
                fixtures = res.get('response', [])
                
                if not fixtures:
                    continue
                
                log("INFO", f"✅ Liga {l_id}: {len(fixtures)} jogos hoje. Filtrando horários...")
                
                for f in fixtures:
                    status = f['fixture']['status']['short']
                    data_jogo = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00')).astimezone(fuso_br)
                    t1_n = f['teams']['home']['name']
                    t2_n = f['teams']['away']['name']

                    if status != "NS":
                        log("JOGO-SKIP", f"Pulando {t1_n} x {t2_n} (Status: {status})")
                        continue
                    
                    if agora_br < data_jogo <= limite_3h:
                        log("JANELA-HIT", f"ADICIONADO: {t1_n} x {t2_n} às {data_jogo.strftime('%H:%M')}")
                        jogos_na_janela.append({
                            "id": f['fixture']['id'],
                            "t1": f['teams']['home'],
                            "t2": f['teams']['away'],
                            "hora_obj": data_jogo,
                            "hora_str": data_jogo.strftime("%H:%M"),
                            "liga": f['league']['name']
                        })
                
                time.sleep(6.1) # Respeitar 10 req/min
                break 
            except Exception as e:
                log("ERRO-LOOP", f"Erro na liga {l_id}: {e}")
                continue

    if not jogos_na_janela:
        log("FIM", "ℹ️ Nenhum jogo encontrado na janela de 3 horas para as ligas monitoradas.")
        return

    log("PROCESSAMENTO", f"Total de {len(jogos_na_janela)} jogos na janela. Analisando Top 15 por horário...")
    jogos_na_janela.sort(key=lambda x: x['hora_obj'])
    top_selecao = jogos_na_janela[:15]

    pool_gols = []

    for j in top_selecao:
        o15_t1 = get_over_stats_5(j['t1']['id'], j['t1']['name'], 1.5)
        time.sleep(6.1)
        o15_t2 = get_over_stats_5(j['t2']['id'], j['t2']['name'], 1.5)
        time.sleep(6.1)
        
        probabilidade = (o15_t1 + o15_t2) / 2
        log("RESULTADO", f"{j['t1']['name']} x {j['t2']['name']}: {probabilidade}% Over 1.5")
        
        pool_gols.append({
            "info": f"*{j['t1']['name']} x {j['t2']['name']}*",
            "hora": j['hora_str'],
            "liga": j['liga'],
            "perc": probabilidade
        })

    pool_gols.sort(key=lambda x: x['perc'], reverse=True)
    top_10 = pool_gols[:10]

    if not top_10:
        log("FIM", "Sem dados suficientes para gerar o Top 10.")
        return

    log("ENVIO", "Montando mensagem e disparando para o Telegram...")
    msg = f"💰 *CASHOUT 3H - TOP 10 GOLS*\n"
    msg += f"⏰ Janela: {agora_br.strftime('%H:%M')} até {limite_3h.strftime('%H:%M')}\n"
    msg += f"----------------------------------\n\n"

    for i, j in enumerate(top_10, 1):
        msg += f"{i}. 🏟️ {j['info']}\n"
        msg += f"🕒 {j['hora']} | {j['liga']}\n"
        msg += f"⚽ *+1.5 Gols:* ({j['perc']:.0f}%)\n\n"

    msg += "---\n🤖 API-SPORTS Ativa"
    enviar_telegram(msg)
    log("SISTEMA", "🚀 Execução finalizada com sucesso.")

if __name__ == "__main__":
    executar_cashout_3h()
