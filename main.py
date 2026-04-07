import os
import requests
from datetime import datetime

# --- CONFIGURAÇÕES DE AMBIENTE ---
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
API_HOST = os.getenv('WITCH_API_HOST')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# --- SEQUÊNCIA DE ELITE (EUROPA > AMÉRICA > ÁSIA) ---
LIGAS_ELITE = [
    "Champions League", "Europa League", "Conference League", "Premier League", 
    "LaLiga", "Serie A", "Bundesliga", "Ligue 1", "Brasileirão Série A", 
    "Brasileirão Série B", "Copa do Brasil", "Libertadores", "Sudamericana", 
    "Saudi Pro League", "J1 League", "K League 1"
]

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print(mensagem)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"})

def minerar_e_gerar_bilhete():
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": API_HOST}
    
    print("🚀 Iniciando Mineração de Elite...")
    try:
        res_grade = requests.get(f"https://{API_HOST}/live/matches", headers=headers, timeout=15)
        jogos_brutos = res_grade.json().get("matches", [])
    except:
        return print("❌ Erro ao buscar grade.")

    bilhete_final = []
    mercados_contagem = 0

    for jogo in jogos_brutos:
        if mercados_contagem >= 13: break

        home = jogo.get('home_team')
        away = jogo.get('away_team')
        liga = jogo.get('league_name', 'Série A')

        if not any(elite.lower() in liga.lower() for elite in LIGAS_ELITE):
            continue

        # Chamada de Análise (Previsão)
        payload = {"sport": "soccer", "home": home, "away": away}
        res_analise = requests.post(f"https://{API_HOST}/v1/analyze", json=payload, headers=headers)
        
        if res_analise.status_code == 200:
            data = res_analise.json()
            stats_h = data.get('home_stats', {})
            stats_a = data.get('away_stats', {})

            # --- VARIÁVEIS DAS SUAS REGRAS ---
            gols_h = stats_h.get('goals_over_15', 0) # 0 a 5
            gols_a = stats_a.get('goals_over_15', 0) # 0 a 5
            derrotas_h = stats_h.get('losses', 0)
            derrotas_a = stats_a.get('losses', 0)
            ult_h = stats_h.get('last_result') # 'W', 'D', 'L'
            ult_a = stats_a.get('last_result')

            mercados_jogo = []

            # --- REGRA DE GOLS (4/5 e 5/5) ---
            # 5/5 e 5/5 -> 100%
            if gols_h == 5 and gols_a == 5:
                mercados_jogo.append("🔶 ⚽ +1.5 Gols (100%)")
                mercados_jogo.append("🔶 ⚽ +2.5 Gols (100%)")
            # 5/5 e 4/5 -> 85%
            elif (gols_h == 5 and gols_a == 4) or (gols_h == 4 and gols_a == 5):
                mercados_jogo.append("🔶 ⚽ +1.5 Gols (85%)")
            # 4/5 e 4/5 -> 75%
            elif gols_h == 4 and gols_a == 4:
                mercados_jogo.append("🔶 ⚽ +1.5 Gols (75%)")

            # --- REGRA 1X (MANDANTE) ---
            if derrotas_h <= 1 and ult_h == 'W':
                if derrotas_a >= 2 and ult_a == 'L':
                    mercados_jogo.append("🔶 🛡️ 1X (100%)")

            # --- REGRA 2X (VISITANTE) ---
            if derrotas_a == 0:
                if derrotas_h >= 2 and ult_h == 'L':
                    mercados_jogo.append("🔶 🛡️ 2X (100%)")

            # Adiciona ao bilhete respeitando o limite de 3 por jogo
            if mercados_jogo:
                bilhete_final.append({
                    "time": f"{home} x {away}",
                    "hora": jogo.get('start_time', 'Hoje'),
                    "liga": liga,
                    "mercados": mercados_jogo[:3]
                })
                mercados_contagem += len(mercados_jogo[:3])

    # --- MONTAGEM DO FRONT-END DO BILHETE ---
    if not bilhete_final: return print("⚠️ Sem jogos na grade hoje.")

    texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, item in enumerate(bilhete_final, 1):
        texto += f"{i}. 🏟️ *{item['time']}*\n"
        texto += f"🕒 {item['hora']} | {item['liga']}\n"
        for m in item['mercados']:
            texto += f"{m}\n"
        texto += "\n"
    
    texto += "---\n💸 *Bet365 | Betano*"
    enviar_telegram(texto)

if __name__ == "__main__":
    minerar_e_gerar_bilhete()
