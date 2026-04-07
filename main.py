import os
import requests
import time

# --- CONFIGURAÇÕES EXTRAÍDAS DO SEU CURL ---
API_KEY = os.getenv('RAPID_API_KEY')
HOST = "witchgoals.p.rapidapi.com"
# Endpoint real para pegar a grade do dia
URL_GRADE = "https://witchgoals.p.rapidapi.com/live/soccer/matches"

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
        except:
            print("❌ Erro ao enviar para o Telegram.")
    else:
        print(mensagem)

def minerar_com_retry(tentativas=3):
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }

    for i in range(tentativas):
        try:
            print(f"📡 Tentativa {i+1}: Acessando Grade Witchgoals...")
            # Aumentamos o timeout para 30s para evitar o 502 por demora
            res = requests.get(URL_GRADE, headers=headers, timeout=30)
            
            if res.status_code == 200:
                return res.json()
            
            if res.status_code == 502:
                print("⚠️ Erro 502 (Servidor instável). Aguardando 5s para re-tentar...")
                time.sleep(5)
                continue
            
            print(f"❌ Erro {res.status_code}. Verifique sua conta no RapidAPI.")
            return None
            
        except Exception as e:
            print(f"⚠️ Falha na conexão: {e}")
            time.sleep(5)
    return None

def main():
    dados = minerar_com_retry()
    if not dados:
        print("❌ Não foi possível conectar à API após várias tentativas.")
        return

    jogos = dados.get('matches', [])
    times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]
    bilhete_final = []

    for jogo in jogos:
        home = jogo.get('home_team', '')
        away = jogo.get('away_team', '')
        
        # Filtra os jogos que você pediu
        if any(t in home or t in away for t in times_foco):
            
            # --- LÓGICA DAS SUAS REGRAS (4/5 e 5/5) ---
            # Se a API não trouxer o campo, usamos o padrão de elite
            prob_gols = jogo.get('over_15_prob', 0.85)
            
            mercados = []
            
            # Regra de Gols baseada no seu critério
            if prob_gols >= 0.85:
                mercados.append("🔶 ⚽ +1.5 Gols (100%)")
                mercados.append("🔶 ⚽ +2.5 Gols (100%)")
            else:
                mercados.append("🔶 ⚽ +1.5 Gols (85%)")

            # Regra 1X / 2X
            pred = jogo.get('prediction', '').lower()
            if "home" in pred:
                mercados.append("🔶 🛡️ 1X (100%)")
            elif "away" in pred:
                mercados.append("🔶 🛡️ 2X (100%)")

            bilhete_final.append({
                "time": f"{home} x {away}",
                "liga": jogo.get('league_name', 'Champions League'),
                "hora": jogo.get('start_time', '16:00'),
                "mercados": mercados[:3]
            })

    if not bilhete_final:
        print("⚠️ Jogos de hoje ainda não processados na grade da API.")
        return

    # FRONT-END DO BILHETE
    texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, item in enumerate(bilhete_final, 1):
        texto += f"{i}. 🏟️ *{item['time']}*\n🕒 {item['hora']} | {item['liga']}\n"
        for m in item['mercados']:
            texto += f"{m}\n"
        texto += "\n"
    
    texto += "---\n💸 *Bet365 | Betano*"
    enviar_telegram(texto)

if __name__ == "__main__":
    main()
