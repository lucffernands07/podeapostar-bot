import os
import tls_client
import requests
import json
import time # Adicionado para o Timestamp
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

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
    # Adicionamos um timestamp (_=123456) que é como o site real faz
    timestamp = int(time.time() * 1000)
    url = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}?_={timestamp}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "x-requested-with": "XMLHttpRequest", # ESSENCIAL: Diz ao site que é uma chamada de dados
        "Cache-Control": "no-cache"
    }

    print(f"📡 Tentando técnica Mkzz1 (URL com Timestamp + XMLHttpRequest)...")
    
    try:
        # Passo 1: Visitar a home para validar a sessão
        session.get("https://www.sofascore.com/", headers=headers)
        
        # Passo 2: Buscar os dados reais
        res = session.get(url, headers=headers)
        
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ Falha: Status {res.status_code}")
            # Se der 404 de novo, tentamos a URL sem o WWW (API pura)
            url_api = f"https://api.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
            res_api = session.get(url_api, headers=headers)
            if res_api.status_code == 200:
                return res_api.json()
            return None
    except Exception as e:
        print(f"⚠️ Erro de Conexão: {e}")
        return None

def main():
    dados = obter_dados()
    if dados:
        eventos = dados.get('events', [])
        print(f"✅ Sucesso! {len(eventos)} jogos encontrados.")
        
        # Seus times favoritos
        times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern", "Corinthians"]
        achados = []

        for ev in eventos:
            # Pegamos o nome do time da casa e de fora
            n_h = ev.get('homeTeam', {}).get('name', '')
            n_a = ev.get('awayTeam', {}).get('name', '')
            
            if any(t.lower() in n_h.lower() or t.lower() in n_a.lower() for t in times_foco):
                hora = datetime.fromtimestamp(ev['startTimestamp']).strftime("%H:%M")
                achados.append(f"🏟️ *{n_h} x {n_a}*\n🕒 {hora}")

        if achados:
            msg = "🎯 *BILHETE DE ELITE ENCONTRADO!*\n\n" + "\n\n".join(achados)
            enviar_telegram(msg)
            print("✅ Bilhete enviado!")
        else:
            print("⚠️ Nenhum jogo dos seus times hoje.")
    else:
        print("❌ O bloqueio persiste.")

if __name__ == "__main__":
    main()
