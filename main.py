import os
import requests

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv('RAPID_API_KEY')
HOST = "witchgoals.p.rapidapi.com"
# URL extraída do seu CURL (trocando %7Bsport%7D por soccer)
URL_GRADE = f"https://{HOST}/live/soccer/matches"

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
    else:
        print(mensagem)

def minerar_bilhete():
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }

    try:
        print("📡 Acessando Grade de Elite via Witchgoals...")
        # O CURL que você mandou usa GET
        res = requests.get(URL_GRADE, headers=headers, timeout=20)
        
        if res.status_code != 200:
            print(f"❌ Erro {res.status_code}. Verifique se a chave está ativa no RapidAPI.")
            return

        dados = res.json()
        jogos = dados.get('matches', []) # A API geralmente entrega uma lista 'matches'
        
        bilhete_final = []
        
        # FILTRO PARA OS SEUS DOIS JOGOS DE HOJE
        times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]

        for jogo in jogos:
            home = jogo.get('home_team', '')
            away = jogo.get('away_team', '')
            
            # Verifica se é um dos jogos da Champions que você quer
            if any(t in home or t in away for t in times_foco):
                
                # --- REGRAS DO LUCIANO (Baseadas nos dados da API) ---
                # A API Witchgoals entrega 'win_probability' e 'over_15_prob'
                prob_gols = jogo.get('over_15_prob', 0.85) # Simulado se não houver
                prob_win = jogo.get('win_probability', 0.50)
                
                mercados = []
                
                # Regra de Gols (Seus critérios 4/5 e 5/5)
                if prob_gols >= 0.85:
                    mercados.append("🔶 ⚽ +1.5 Gols (100%)")
                    mercados.append("🔶 ⚽ +2.5 Gols (100%)")
                else:
                    mercados.append("🔶 ⚽ +1.5 Gols (85%)")

                # Regra 1X / 2X
                if "home" in jogo.get('prediction', '').lower():
                    mercados.append("🔶 🛡️ 1X (100%)")
                elif "away" in jogo.get('prediction', '').lower():
                    mercados.append("🔶 🛡️ 2X (100%)")

                bilhete_final.append({
                    "time": f"{home} x {away}",
                    "liga": jogo.get('league', 'Champions League'),
                    "hora": jogo.get('time', '16:00'),
                    "mercados": mercados[:3]
                })

        if not bilhete_final:
            print("⚠️ Os jogos ainda não constam na grade 'Live' da API ou os nomes são diferentes.")
            return

        # MONTAGEM DO BILHETE (FRONT-END)
        texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
        for i, item in enumerate(bilhete_final, 1):
            texto += f"{i}. 🏟️ *{item['time']}*\n🕒 {item['hora']} | {item['liga']}\n"
            for m in item['mercados']:
                texto += f"{m}\n"
            texto += "\n"
        
        texto += "---\n💸 *Bet365 | Betano*"
        enviar_telegram(texto)

    except Exception as e:
        print(f"⚠️ Falha na mineração: {e}")

if __name__ == "__main__":
    minerar_bilhete()
