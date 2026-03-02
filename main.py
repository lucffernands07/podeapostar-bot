import os
import requests
from bs4 import BeautifulSoup
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try:
        requests.get(url)
    except:
        pass

def analisar_detalhes(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        texto_pagina = soup.get_text().lower()

        # Detetive de Escalação
        status_time = "✅ Titulares"
        if any(word in texto_pagina for word in ["reserva", "poupado", "desfalques", "injury", "ausentes"]):
            status_time = "⚠️ Atenção: Reservas"

        # Lógica Focada em Mínimo de 2 Gols (Over 1.5)
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total_jogos = len(placares)
        jogos_over_1_5 = 0
        
        for p in placares:
            try:
                gols = sum(map(int, p.split('-')))
                if gols >= 2: # Foco total em 2 gols ou mais
                    jogos_over_1_5 += 1
            except:
                continue
        
        prob = (jogos_over_1_5 / total_jogos) if total_jogos > 0 else 0
        return prob, status_time
    except:
        return 0, "❌ Erro"

def executar_robo():
    enviar_telegram("🎯 *PodeApostar_Bot:* Varredura para Mínimo 2 Gols Iniciada!")
    
    url_base = "https://www.placardefutebol.com.br"
    ligas = [
        "/brasileirao-serie-a",
        "/campeonato-ingles",
        "/campeonato-italiano",
        "/campeonato-espanhol",
        "/campeonato-portugues",
        "/campeonato-argentino" # <--- Campeonato Argentino Adicionado!
    ]
    
    total_encontrados = 0

    for liga in ligas:
        try:
            response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) < 2: continue
                    
                    casa, fora = times[0].text, times[1].text
                    prob, status = analisar_detalhes(url_base + link['href'])
                    
                    # Filtro calibrado para te dar mais opções (Volume para sua múltipla)
                    if prob >= 0.35:
                        msg = (f"🏆 *{liga.replace('/','').upper()}*\n"
                               f"🏟️ {casa} x {fora}\n"
                               f"📈 Chance +1.5 Gols: {prob*100:.0f}%\n"
                               f"📋 Info: {status}\n"
                               f"🚀 *Sugestão:* Mínimo 2 Gols")
                        enviar_telegram(msg)
                        total_encontrados += 1
                    time.sleep(1)
        except:
            continue

    if total_encontrados == 0:
        enviar_telegram("🔍 Sem jogos com tendência de 2 gols hoje.")

if __name__ == "__main__":
    executar_robo()
    
