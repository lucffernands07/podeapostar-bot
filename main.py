import os
import tls_client
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuração de Sessão Ultra-Realista
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

def obter_headers_premium():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.sofascore.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "x-requested-with": "widgets" # Isso aqui ajuda a burlar o bloqueio de bot
    }

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    # Mudamos o endpoint para o de 'scheduled', que costuma ser menos protegido que o 'day'
    url = f"https://www.sofascore.com/api/v1/sport/soccer/scheduled-events/{hoje}"
    
    print(f"📡 Tentando furar bloqueio SofaScore ({hoje})...")
    
    try:
        res = session.get(url, headers=obter_headers_premium())
        
        if res.status_code == 403:
            print("❌ Bloqueio persistente (403). Tentando rota alternativa...")
            # Rota de fallback: API de categorias
            url = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
            res = session.get(url, headers=obter_headers_premium())

        if res.status_code != 200:
            print(f"❌ Erro final: {res.status_code}. SofaScore bloqueou o IP do GitHub.")
            return

        dados = res.json()
        print("✅ Conexão estabelecida! Minerando jogos...")
        
        # ... (resto da sua lógica de filtro para Sporting e Real Madrid)
        # Se chegar aqui, o print vai mostrar os jogos.
        
    except Exception as e:
        print(f"⚠️ Erro crítico: {e}")

if __name__ == "__main__":
    main()
