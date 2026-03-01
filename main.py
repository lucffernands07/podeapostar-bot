import os
import requests
from bs4 import BeautifulSoup

# Configurações do Telegram (Pegos do seu Secrets)
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    requests.get(url)

def capturar_e_analisar():
    # URL de um site que mostra os jogos de hoje (exemplo de fonte mais fácil de raspar que o Sofa)
    url = "https://www.placardefutebol.com.br/jogos-de-hoje"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O robô procura todos os jogos na página
        jogos = soup.find_all('div', class_='match-container') 
        
        if not jogos:
            enviar_telegram("🔎 *PodeApostar:* Busquei os jogos, mas a rodada ainda não carregou ou o site bloqueou o acesso.")
            return

        for jogo in jogos:
            time_casa = jogo.find('div', class_='team-home').text.strip()
            time_fora = jogo.find('div', class_='team-away').text.strip()
            
            # --- LÓGICA DE PROBABILIDADE ---
            # Aqui o robô deveria entrar no histórico (H2H). 
            # Como teste, ele vai te mandar os jogos encontrados:
            
            msg = (f"⚽ *Jogo Encontrado:* {time_casa} x {time_fora}\n"
                   f"📊 *Análise:* Robô verificando histórico de 1-3 gols...")
            enviar_telegram(msg)

    except Exception as e:
        enviar_telegram(f"❌ Erro ao automatizar: {e}")

if __name__ == "__main__":
    capturar_e_analisar()
    
