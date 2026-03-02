import os
import requests
from bs4 import BeautifulSoup
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    requests.get(url)

def analisar_detalhes(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        texto_pagina = soup.get_text().lower()

        # Lógica de Escalação
        status_time = "✅ Titulares Prováveis"
        if any(word in texto_pagina for word in ["reserva", "poupado", "desfalques", "injury", "substitute"]):
            status_time = "⚠️ Atenção: Possíveis Desfalques!"

        # Lógica de Gols (H2H)
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        gols_no_range = sum(1 for p in placares if 1 <= sum(map(int, p.split('-'))) <= 3)
        
        prob = (gols_no_range / len(placares)) if placares else 0
        return prob, status_time
    except:
        return 0, "❌ Erro na análise"

def executar_robo():
    enviar_telegram("🌍 *PodeApostar_Bot:* Iniciando Varredura Internacional (BRA, ING, ITA)...")
    
    url_base = "https://www.placardefutebol.com.br"
    # Lista de ligas para o robô monitorar
    ligas = [
        "/brasileirao-serie-a",
        "/campeonato-ingles",
        "/campeonato-italiano"
    ]
    
    total_encontrados = 0

    for liga in ligas:
        response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            if '/jogo/' in link['href']:
                times = link.find_all('span', class_='team-name')
                if len(times) < 2: continue
                
                casa, fora = times[0].text, times[1].text
                prob, status = analisar_detalhes(url_base + link['href'])
                
                if prob >= 0.5:
                    msg = (f"🏆 *{liga.replace('/','').upper()}*\n"
                           f"🏟️ {casa} x {fora}\n"
                           f"📈 Tendência 1-3 Gols: {prob*100:.0f}%\n"
                           f"📋 Info: {status}\n"
                           f"🎯 Sugestão: 1-3 Gols & HT")
                    enviar_telegram(msg)
                    total_encontrados += 1
                time.sleep(1)

    if total_encontrados == 0:
        enviar_telegram("Checking... Sem padrões de 1-3 gols nas ligas principais hoje.")

if __name__ == "__main__":
    executar_robo()
