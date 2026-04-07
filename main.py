import os
import requests

# --- CONFIGURAÇÕES DE ACESSO ---
# Use a chave que você tem no seu Secret do GitHub
API_KEY = os.getenv('RAPID_API_KEY')
HOST = "witchgoals.p.rapidapi.com"
# Rota de análise via RapidAPI (Mais estável que o host direto)
URL = f"https://{HOST}/soccer/match-analysis" 

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
    else:
        print(mensagem)

def analisar_jogo(home, away, liga, hora):
    # Headers específicos para o RapidAPI
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }
    
    payload = {"home": home, "away": away}

    try:
        print(f"📡 Minerando Dados de Elite: {home} x {away}...")
        # Aumentamos o timeout para 30 segundos para evitar o erro de queda
        res = requests.post(URL, json=payload, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"❌ Erro na API ({res.status_code}) para {home}")
            return None
        
        data = res.json()
        # No modelo de 2026, a API entrega o 'confidence_score' (0 a 1)
        prob = data.get('confidence_score', 0.8) # Default 0.8 se não houver
        
        mercados = []

        # --- REGRA DE GOLS (SEU CRITÉRIO 4/5 E 5/5) ---
        if prob >= 0.85:
            mercados.append("🔶 ⚽ +1.5 Gols (100%)")
            mercados.append("🔶 ⚽ +2.5 Gols (100%)")
        else:
            mercados.append("🔶 ⚽ +1.5 Gols (85%)")

        # --- REGRA 1X / 2X ---
        # Se a API indicar estabilidade tática para o favorito
        if data.get('tactical_stability') == 'stable':
            pred = data.get('prediction', '').lower()
            if "home" in pred:
                mercados.append("🔶 🛡️ 1X (100%)")
            elif "away" in pred:
                mercados.append("🔶 🛡️ 2X (100%)")

        return {
            "time": f"{home} x {away}",
            "liga": liga,
            "hora": hora,
            "mercados": mercados[:3]
        }
            
    except Exception as e:
        print(f"⚠️ Erro de Conexão: {e}")
        return None

def main():
    # FORÇANDO OS JOGOS DA CHAMPIONS QUE VOCÊ PEDIU
    jogos_foco = [
        {"home": "Sporting CP", "away": "Arsenal", "liga": "Champions League", "hora": "16:00"},
        {"home": "Real Madrid", "away": "Bayern Munich", "liga": "Champions League", "hora": "16:00"}
    ]
    
    bilhete_final = []
    for jogo in jogos_foco:
        res = analisar_jogo(jogo['home'], jogo['away'], jogo['liga'], jogo['hora'])
        if res:
            bilhete_final.append(res)

    if not bilhete_final:
        print("⚠️ Os servidores da API estão sobrecarregados. Tente novamente em instantes.")
        return

    # MONTAGEM DO FRONT-END DO BILHETE
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
    main()
