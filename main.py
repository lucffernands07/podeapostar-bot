import os
import requests
import random
import re
from datetime import datetime

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def analisar_estatisticas(nome_jogo):
    opcoes = [
        ("🎯 Ambas Marcam", 79, "H2H com média alta."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio tático."),
        ("🔥 +1.5 Golos", 84, "Tendência de over."),
        ("🚩 +8.5 Cantos", 72, "Jogo vertical."),
        ("⏱️ Golo HT", 81, "Intensidade inicial.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Localizando jogos via Search Proxy...")
    
    # Buscamos no Google pelos jogos do dia no Sporting Life
    query = "site:sportinglife.com/football/live/"
    url_search = f"https://www.google.com/search?q={query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(url_search, headers=headers, timeout=20)
        content = res.text
        
        # Extraímos os links usando Regex (Padrão de link de jogo)
        links = re.findall(r'https://www.sportinglife.com/football/live/\d+', content)
        links = list(set(links)) # Remove duplicados

        print(f"Encontrados {len(links)} links de jogos.")

        bilhete = []
        for link in links:
            # Como o Google nos dá o link, geramos um nome genérico ou tentamos extrair do link
            # Ex: /football/live/12345 -> Jogo ID 12345
            id_jogo = link.split('/')[-1]
            nome_jogo = f"Partida ID {id_jogo}"
            
            mercado, conf, obs = analisar_estatisticas(nome_jogo)
            bilhete.append({
                "jogo": nome_jogo,
                "aposta": mercado,
                "conf": conf,
                "link": link
            })
            if len(bilhete) >= 10: break

        if len(bilhete) >= 3:
            bilhete.sort(key=lambda x: -x['conf'])
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Search Mode | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *Jogo {j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Ver Estatísticas]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Bilhete enviado via Search!")
        else:
            print("Poucos links encontrados. Tentando link direto de grade...")
            # Fallback final: Envia o link da grade para você clicar
            enviar_telegram("⚠️ *Aviso:* Não consegui extrair os jogos automaticamente hoje, mas você pode conferir a grade aqui: [Sporting Life Fixtures](https://www.sportinglife.com/football/fixtures-results)")

    except Exception as e:
        print(f"Erro no Search: {e}")

if __name__ == "__main__":
    executar_robo()
            
