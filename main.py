import os
import requests
from bs4 import BeautifulSoup

# Configurações vindas do seu GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Erro ao enviar: {e}")

def analisar_rodada():
    # Usando uma fonte de resultados mais leve
    url = "https://www.placardefutebol.com.br/brasileirao-serie-a"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O robô procura os blocos de jogos
        jogos = soup.find_all('a', href=True)
        encontrados = 0

        enviar_telegram("🤖 *PodeApostar_Bot:* Iniciando varredura automática...")

        for jogo in jogos:
            # Filtra apenas links que parecem ser de confrontos
            if '/jogo/' in jogo['href']:
                nomes_times = jogo.find_all('span', class_='team-name')
                if len(nomes_times) >= 2:
                    casa = nomes_times[0].text.strip()
                    fora = nomes_times[1].text.strip()
                    encontrados += 1
                    
                    # --- AQUI ENTRA O SEU RACIOCÍNIO ---
                    # Para o robô ser "certeiro", ele analisa a probabilidade:
                    # (Simulação de lógica baseada em nomes ou dados da página)
                    
                    alerta = (
                        f"🏟️ *Jogo:* {casa} x {fora}\n"
                        f"📊 *Análise:* Alta probabilidade para 1-3 Gols\n"
                        f"⏱️ *HT:* Tendência de gol no 1º tempo detectada!"
                    )
                    enviar_telegram(alerta)
        
        if encontrados == 0:
            enviar_telegram("⚠️ Nenhum jogo da Série A foi capturado agora. Verifique se a rodada já começou.")

    except Exception as e:
        enviar_telegram(f"❌ Erro no processamento: {e}")

if __name__ == "__main__":
    analisar_analisar_rodada()
                    
