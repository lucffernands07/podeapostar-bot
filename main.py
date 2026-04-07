import os
import tls_client
import json
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis do .env ou GitHub Secrets
load_dotenv()

# --- CONFIGURAÇÕES DE CONEXÃO ---
# Criamos a sessão que imita o Chrome 120 para não ser bloqueado
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com"
}

# --- REGRAS DO LUCIANO ---
TIMES_FOCO = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        # Usamos requests simples aqui pois a API do Telegram não bloqueia
        import requests
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
    else:
        print(mensagem)

def calcular_metricas_time(team_id):
    """Analisa os últimos 5 jogos para validar a regra 4/5 e 5/5"""
    url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/last/0"
    try:
        res = session.get(url, headers=HEADERS)
        if res.status_code != 200: return 0, 0, False
        
        jogos = res.json().get('events', [])[:5]
        over_15 = 0
        derrotas = 0
        venceu_ultimo = False

        for i, jogo in enumerate(jogos):
            h_score = jogo.get('homeScore', {}).get('display', 0)
            a_score = jogo.get('awayScore', {}).get('display', 0)
            
            # Regra de Gols
            if (h_score + a_score) >= 2: over_15 += 1
            
            # Regra de Vitória/Derrota
            sou_home = jogo['homeTeam']['id'] == team_id
            ganhou = (sou_home and h_score > a_score) or (not sou_home and a_score > h_score)
            perdeu = (sou_home and h_score < a_score) or (not sou_home and a_score < h_score)

            if perdeu: derrotas += 1
            if i == 0 and ganhou: venceu_ultimo = True

        return over_15, derrotas, venceu_ultimo
    except:
        return 0, 0, False

def main():
    # Data de hoje (Formato SofaScore: 2026-04-07)
    hoje = datetime.now().strftime("%Y-%m-%d")
    url_dia = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    print(f"📡 Minerando SofaScore: {hoje}...")
    res = session.get(url_dia, headers=HEADERS)
    
    if res.status_code != 200:
        print(f"❌ Bloqueio Detectado (Status {res.status_code})")
        return

    eventos = res.json().get('events', [])
    bilhete = []

    for ev in eventos:
        home_n, away_n = ev['homeTeam']['name'], ev['awayTeam']['name']
        
        # Filtro de Elite
        if any(t in home_n or t in away_n for t in TIMES_FOCO):
            print(f"🏟️ Analisando: {home_n} x {away_n}")
            
            g_h, d_h, v_h = calcular_metricas_time(ev['homeTeam']['id'])
            g_a, d_a, v_a = calcular_metricas_time(ev['awayTeam']['id'])
            
            mercados = []

            # --- LÓGICA DE GOLS (4/5 e 5/5) ---
            if g_h == 5 and g_a == 5:
                mercados.append("🔶 ⚽ +1.5 Gols (100%)")
                mercados.append("🔶 ⚽ +2.5 Gols (100%)")
            elif (g_h >= 4 and g_a >= 5) or (g_h >= 5 and g_a >= 4):
                mercados.append("🔶 ⚽ +1.5 Gols (85%)")
            elif g_h >= 4 and g_a >= 4:
                mercados.append("🔶 ⚽ +1.5 Gols (75%)")

            # --- LÓGICA 1X / 2X ---
            # Exemplo: Mandante forte (max 1 derrota) x Visitante em crise (min 2 derrotas)
            if d_h <= 1 and v_h and d_a >= 2:
                mercados.append("🔶 🛡️ 1X (100%)")
            elif d_a == 0 and d_h >= 2:
                mercados.append("🔶 🛡️ 2X (100%)")

            if mercados:
                bilhete.append({
                    "jogo": f"{home_n} x {away_n}",
                    "liga": ev['tournament']['name'],
                    "hora": datetime.fromtimestamp(ev['startTimestamp']).strftime("%H:%M"),
                    "mercados": mercados[:3]
                })

    # MONTAGEM DO BILHETE FINAL
    if not bilhete:
        print("⚠️ Nenhum jogo atingiu os critérios técnicos hoje.")
        return

    texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, item in enumerate(bilhete, 1):
        texto += f"{i}. 🏟️ *{item['jogo']}*\n🕒 {item['hora']} | {item['liga']}\n"
        for m in item['mercados']: texto += f"{m}\n"
        texto += "\n"
    texto += "---\n💸 *Bet365 | Betano*"
    
    enviar_telegram(texto)
    print("✅ Bilhete enviado com sucesso!")

if __name__ == "__main__":
    main()
