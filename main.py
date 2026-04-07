import os
import tls_client
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Sessão simulando um iPhone antigo (mais estável para a API)
session = tls_client.Session(client_identifier="chrome_120")

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # URL OFICIAL DA API MOBILE (Sem o 'www')
    url = f"https://api.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    # Headers que o App oficial do SofaScore envia
    headers = {
        "User-Agent": "SofaScore/6.1.1 (iPhone; iOS 17.4.1; Scale/3.00)",
        "Accept": "*/*",
        "Host": "api.sofascore.com",
        "Connection": "keep-alive",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }

    print(f"📡 Tentando Rota Mobile Segura ({hoje})...")
    
    try:
        res = session.get(url, headers=headers)
        
        if res.status_code == 200:
            print("✅ Conexão estabelecida via API Mobile!")
            eventos = res.json().get('events', [])
            
            # FILTRO DO LUCIANO (Sporting, Arsenal, Real, Bayern)
            times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]
            bilhete = []

            for ev in eventos:
                h_name = ev['homeTeam']['name']
                a_name = ev['awayTeam']['name']
                
                if any(t in h_name or t in a_name for t in times_foco):
                    # Aqui você pode adicionar a lógica de 4/5 e 5/5
                    bilhete.append(f"🏟️ {h_name} x {a_name}")

            if bilhete:
                enviar_telegram("🎯 *JOGOS DE HOJE ENCONTRADOS:*\n\n" + "\n".join(bilhete))
                print("✅ Bilhete enviado!")
            else:
                print("⚠️ Jogos de elite ainda não listados.")
                
        else:
            print(f"❌ Falha na Rota Mobile: {res.status_code}")
            if res.status_code == 403:
                print("💡 Dica: O SofaScore baniu o IP do GitHub temporariamente.")

    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
