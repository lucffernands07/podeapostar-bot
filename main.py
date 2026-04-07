import os
import tls_client
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (Secrets do GitHub)
load_dotenv()

# Sessão com assinatura Chrome 120 (a mais estável hoje)
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        # Para o Telegram, o requests comum é seguro e não bloqueia
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def obter_dados():
    hoje = datetime.now().strftime("%Y-%m-%d")
    # A URL atualizada que o site e o app estão usando agora
url = f"https://www.sofascore.com/api/v1/sport/soccer/events/day/{hoje}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }

    print(f"📡 Tentando técnica do fórum (TLS-Client + iPhone Signature)...")
    
    try:
        # Passo 1: "Aquecer" a sessão na Home para gerar cookies básicos
        session.get("https://www.sofascore.com", headers=headers)
        
        # Passo 2: Buscar os dados reais da API
        res = session.get(url, headers=headers)
        
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ Falha: Status {res.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Erro de Conexão: {e}")
        return None

def main():
    dados = obter_dados()
    if dados:
        eventos = dados.get('events', [])
        print(f"✅ Sucesso! {len(eventos)} jogos encontrados no SofaScore.")
        
        # Seus times favoritos (Foco total do Luciano)
        times_foco = ["Sporting", "Arsenal", "Real Madrid", "Bayern", "Corinthians"]
        achados = []

        for ev in eventos:
            n_h = ev['homeTeam']['name']
            n_a = ev['awayTeam']['name']
            
            if any(t in n_h or t in n_a for t in times_foco):
                # Formata a hora do jogo (Timestamp para HH:MM)
                hora = datetime.fromtimestamp(ev['startTimestamp']).strftime("%H:%M")
                achados.append(f"🏟️ *{n_h} x {n_a}*\n🕒 {hora}")

        if achados:
            msg = "🎯 *BILHETE DE ELITE ENCONTRADO!*\n\n" + "\n\n".join(achados)
            enviar_telegram(msg)
            print("✅ Bilhete enviado com sucesso!")
        else:
            print("⚠️ Nenhum jogo dos times foco para hoje.")
    else:
        print("❌ O bloqueio persiste. Tentaremos novamente no próximo agendamento.")

if __name__ == "__main__":
    main()
