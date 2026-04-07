import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        # Usamos o requests normal aqui pois o Telegram não bloqueia o GitHub
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def buscar_com_scraperant(url_alvo):
def buscar_com_scraperant(url_alvo):
    api_key = os.getenv('SCRAPERANT_API_KEY')
    # Endpoint oficial do ScrapingAnt
    proxy_url = "https://api.scrapingant.com/v2/general"
    
    params = {
        "url": url_alvo,
        "x-api-key": api_key,
        "browser": "false" 
    }
    
    print(f"📡 Minerando via ScrapingAnt...")
    try:
        res = requests.get(proxy_url, params=params, timeout=30)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ Erro ScrapingAnt: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"⚠️ Erro na conexão: {e}")
        return None

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    # URL que o ScraperAnt vai acessar por nós
    url_sofascore = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    dados = buscar_com_scraperant(url_sofascore)
    
    if dados:
        eventos = dados.get('events', [])
        print(f"✅ Sucesso! {len(eventos)} jogos recebidos.")
        
        times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern", "Corinthians"]
        bilhete = []

        for ev in eventos:
            h_name = ev['homeTeam']['name']
            a_name = ev['awayTeam']['name']
            
            if any(t in h_name or t in a_name for t in times_foco):
                # Formata a hora do jogo (timestamp para HH:MM)
                hora = datetime.fromtimestamp(ev['startTimestamp']).strftime("%H:%M")
                bilhete.append(f"🏟️ *{h_name} x {a_name}*\n🕒 {hora}")

        if bilhete:
            msg = "🎯 *BILHETE DO DIA (SofaScore)*\n\n" + "\n\n".join(bilhete)
            enviar_telegram(msg)
            print("✅ Mensagem enviada para o Telegram!")
        else:
            print("⚠️ Nenhum dos times foco joga hoje.")
    else:
        print("❌ Falha ao obter dados do dia.")

if __name__ == "__main__":
    main()
