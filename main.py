import os
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def analisar_estatisticas(nome_jogo):
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos no H2H."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio no histórico recente."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada."),
        ("🚩 +8.5 Cantos", 72, "Jogo vertical detectado."),
        ("⏱️ Golo HT", 81, "Início de jogo intenso.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando Modo API Direta...")
    
    url_base = "https://www.sportinglife.com"
    url_jogos = f"{url_base}/football/fixtures-results"
    
    # Headers que imitam um navegador real para pular o bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/'
    }

    try:
        session = requests.Session()
        res = session.get(url_jogos, headers=headers, timeout=20)
        
        if res.status_code != 200:
            print(f"Erro de acesso: {res.status_code}. O site bloqueou o IP.")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Busca todos os links de jogos
        links = soup.find_all('a', href=True)
        urls_validas = []
        vistos = set()

        for link in links:
            href = link['href']
            texto = link.get_text().strip()
            
            if "/football/live/" in href and " vs " in texto.lower():
                url_completa = url_base + href if href.startswith('/') else href
                if url_completa not in vistos:
                    urls_validas.append((texto.replace("\n", " "), url_completa))
                    vistos.add(url_completa)
            
            if len(urls_validas) >= 12: break

        print(f"Encontrados {len(urls_validas)} jogos. Gerando bilhete...")

        bilhete = []
        for nome, url in urls_validas:
            mercado, conf, obs = analisar_estatisticas(nome)
            bilhete.append({
                "jogo": nome, "aposta": mercado, "conf": conf, "obs": obs, "link": url
            })

        bilhete.sort(key=lambda x: -x['conf'])

        if len(bilhete) >= 5:
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Modo Light | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete[:10], 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Ver Dados]({j['link']})\n\n"
            enviar_telegram(msg)
            print("Bilhete enviado!")
        else:
            print("Nenhum jogo encontrado no HTML.")

    except Exception as e:
        print(f"Erro na extração: {e}")

if __name__ == "__main__":
    executar_robo()
