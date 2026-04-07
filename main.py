import os
import tls_client
import requests
import json
from datetime import datetime

# Usamos a assinatura do Chrome 120 que é a mais aceita pelo Cloudflare hoje
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def obter_dados():
    hoje = datetime.now().strftime("%Y-%m-%d")
    # A URL mobile (api.sofascore) é a que o pessoal do fórum recomenda
    url = f"https://api.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }

    print(f"📡 Tentando técnica do fórum (TLS-Client + iPhone Signature)...")
    
    try:
        # O segredo do fórum: Fazer um 'GET' na home antes para pegar os cookies
        session.get("https://www.sofascore.com", headers=headers)
        
        # Agora sim buscamos os dados
        res = session.get(url, headers=headers)
        
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ Falha: Status {res.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Erro: {e}")
        return None

def main():
    dados = obter_dados()
    if dados:
        eventos = dados.get('events', [])
        print(f"✅ Sucesso! {len(eventos)} jogos encontrados.")
        
        # Filtro: Sporting, Arsenal, Real, Bayern
        times = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]
        achados = []

        for ev in eventos:
            n_h, n_a = ev['homeTeam']['name'], ev['awayTeam']['name']
            if any(t in n_h or t in n_a for t in times):
                achados.append(f"🏟️ {n_h} x {n_a}")

        if achados:
            enviar_telegram("🎯 *JOGOS DE HOJE:*\n\n" + "\n".join(achados))
    else:
        print("❌ O bloqueio continua. O IP do GitHub pode estar na 'lista negra'.")

if __name__ == "__main__":
    main()
