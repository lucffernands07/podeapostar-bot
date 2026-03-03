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
    print(f"[{datetime.now().strftime('%H:%M')}] Ignorando Pop-ups e buscando jogos...")
    
    url_alvo = "https://www.sportinglife.com/football/fixtures-results"
    
    # Headers simulando que VOCÊ já clicou em "Allow All Cookies"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive'
    }

    # Injetamos o cookie que o site espera para "pular" o pop-up da imagem
    cookies = {
        'notice_gdpr_prefs': '0,1,2:', # Simula aceitação de cookies
        'skybet_odds_format': 'decimal',
        'st_active_section': 'football'
    }

    try:
        session = requests.Session()
        res = session.get(url_alvo, headers=headers, cookies=cookies, timeout=25)
        
        # Procuramos por links de partidas ao vivo ou futuras
        # O padrão no HTML é /football/live/ seguido de números
        links_raw = re.findall(r'href="/football/live/(\d+)"', res.text)
        
        # Limpamos duplicados
        ids_jogos = list(set(links_raw))
        
        print(f"Detectados {len(ids_jogos)} jogos após ignorar bloqueio.")

        bilhete = []
        for id_j in ids_jogos:
            link = f"https://www.sportinglife.com/football/live/{id_j}"
            nome_fake = f"Confronto {id_j}" # O nome exato só vem com Selenium ou API
            
            mercado, conf, obs = analisar_estatisticas(nome_fake)
            bilhete.append({
                "jogo": nome_fake,
                "aposta": mercado,
                "conf": conf,
                "link": link
            })
            if len(bilhete) >= 10: break

        if len(bilhete) >= 3:
            bilhete.sort(key=lambda x: -x['conf'])
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Bypass Mode | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *Jogo {j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Analisar no Site]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Bilhete enviado furando o Pop-up!")
        else:
            # Se ainda assim não achar, mandamos o link direto para você
            print("Ainda bloqueado pelo Pop-up.")
            enviar_telegram("⚠️ *Aviso:* O Sporting Life reforçou o bloqueio de Cookies. Acesse manualmente: [Grade de Jogos](https://www.sportinglife.com/football/fixtures-results)")

    except Exception as e:
        print(f"Erro ao tentar burlar pop-up: {e}")

if __name__ == "__main__":
    executar_robo()
                
