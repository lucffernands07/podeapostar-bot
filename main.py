import os
import requests

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv('RAPID_API_KEY')
HOST = "witchgoals.p.rapidapi.com"
# Ajustado para o padrão de Single Endpoint do RapidAPI
URL = f"https://{HOST}/" 

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    else:
        print(mensagem)

def analisar_jogo(home, away, liga, hora):
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }
    
    # Payload para o "Powerful AI Sports Forecasting Engine"
    payload = {
        "sport": "soccer",
        "home": home,
        "away": away
    }

    try:
        print(f"📡 Consultando Inteligência Witchgoals: {home} x {away}...")
        # Usando POST conforme a maioria das APIs de AI
        res = requests.post(URL, json=payload, headers=headers, timeout=20)
        
        # Se der 404 na raiz, tentamos o endpoint 'analyze' que estava na outra doc
        if res.status_code == 404:
            res = requests.post(f"{URL}analyze", json=payload, headers=headers, timeout=20)

        if res.status_code != 200:
            print(f"❌ Erro {res.status_code}. Verifique o 'Request URL' no Playground da RapidAPI.")
            return None
        
        data = res.json()
        
        # Conforme o print: "probabilities with exact confidence percentages"
        # Os campos comuns nessas APIs são 'probability' ou 'confidence'
        prob = data.get('probability', data.get('confidence', 0))
        pred = data.get('prediction', '').lower()
        
        mercados = []

        # --- REGRAS DO LUCIANO (4/5 e 5/5) ---
        if prob >= 0.85 or "high_confidence" in str(data):
            mercados.append("🔶 ⚽ +1.5 Gols (100%)")
            mercados.append("🔶 ⚽ +2.5 Gols (100%)")
        elif prob >= 0.70:
            mercados.append("🔶 ⚽ +1.5 Gols (85%)")

        # --- REGRAS 1X / 2X ---
        if "home" in pred:
            mercados.append("🔶 🛡️ 1X (100%)")
        elif "away" in pred:
            mercados.append("🔶 🛡️ 2X (100%)")

        if mercados:
            return {"time": f"{home} x {away}", "liga": liga, "hora": hora, "mercados": mercados[:3]}
            
    except Exception as e:
        print(f"⚠️ Erro de conexão: {e}")
        return None

def main():
    # FOCO NOS JOGOS DA CHAMPIONS DE HOJE
    jogos = [
        {"home": "Sporting CP", "away": "Arsenal", "liga": "Champions League", "hora": "16:00"},
        {"home": "Real Madrid", "away": "Bayern Munich", "liga": "Champions League", "hora": "16:00"}
    ]
    
    bilhete = []
    for j in jogos:
        r = analisar_jogo(j['home'], j['away'], j['liga'], j['hora'])
        if r: bilhete.append(r)

    if not bilhete:
        print("⚠️ A API não retornou dados para esses times. Verifique se os nomes estão corretos no Playground.")
        return

    # FRONT-END DO BILHETE
    texto = "🎯 *BILHETE DO DIA*\n💰🍀 *BOA SORTE!!!*\n\n"
    for i, item in enumerate(bilhete, 1):
        texto += f"{i}. 🏟️ *{item['time']}*\n🕒 {item['hora']} | {item['liga']}\n"
        for m in item['mercados']: texto += f"{m}\n"
        texto += "\n"
    texto += "---\n💸 *Bet365 | Betano*"
    
    enviar_telegram(texto)

if __name__ == "__main__":
    main()
