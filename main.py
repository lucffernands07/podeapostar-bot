import os
import tls_client
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Sessão Stealth para pular o bloqueio
session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def obter_metricas(team_id):
    url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/last/0"
    res = session.get(url, headers=HEADERS)
    if res.status_code != 200: return 0, 0
    
    jogos = res.json().get('events', [])[:5]
    over_15 = sum(1 for j in jogos if (j.get('homeScore', {}).get('display', 0) + j.get('awayScore', {}).get('display', 0)) >= 2)
    derrotas = sum(1 for j in jogos if (j['homeTeam']['id'] == team_id and j.get('homeScore', {}).get('display', 0) < j.get('awayScore', {}).get('display', 0)) or (j['awayTeam']['id'] == team_id and j.get('awayScore', {}).get('display', 0) < j.get('homeScore', {}).get('display', 0)))
    return over_15, derrotas

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    url_dia = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    res = session.get(url_dia, headers=HEADERS)
    if res.status_code != 200: return print("❌ Bloqueio SofaScore")

    eventos = res.json().get('events', [])
    times_alvo = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]
    bilhete = []

    for ev in eventos:
        h_name, a_name = ev['homeTeam']['name'], ev['awayTeam']['name']
        if any(t in h_name or t in a_name for t in times_alvo):
            g_h, d_h = obter_metricas(ev['homeTeam']['id'])
            g_a, d_a = obter_metricas(ev['awayTeam']['id'])
            
            mercados = []
            # Regra 4/5 e 5/5
            if g_h >= 4 and g_a >= 4: mercados.append("🔶 ⚽ +1.5 Gols")
            if d_h <= 1 and d_a >= 2: mercados.append("🔶 🛡️ 1X")
            
            if mercados:
                bilhete.append({"jogo": f"{h_name} x {a_name}", "mercados": mercados})

    if bilhete:
        msg = "🎯 *BILHETE DO DIA*\n\n"
        for b in bilhete:
            msg += f"🏟️ *{b['jogo']}*\n" + "\n".join(b['mercados']) + "\n\n"
        enviar_telegram(msg)

if __name__ == "__main__":
    main()
