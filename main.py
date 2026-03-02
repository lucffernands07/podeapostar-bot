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

        # --- LÓGICA DE ESCALAÇÃO ---
        # O robô procura indícios de que o time pode estar desfalcado
        alerta_escalacao = "✅ Titulares Prováveis"
        if "reserva" in texto_pagina or "poupado" in texto_pagina or "desfalques" in texto_pagina:
            alerta_escalacao = "⚠️ ATENÇÃO: Possíveis Desfalques/Reservas detectados!"

        # --- LÓGICA DE GOLS (H2H) ---
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        gols_no_range = 0
        for p in placares:
            try:
                total = sum(map(int, p.split('-')))
                if 1 <= total <= 3: gols_no_range += 1
            except: continue
        
        prob = (gols_no_range / len(placares)) if placares else 0
        return prob, alerta_escalacao
    except:
        return 0, "❌ Erro ao ler escalação"

def executar_robo():
    enviar_telegram("🤖 *PodeApostar_Bot:* Iniciando análise para a rodada!")
    
    url_base = "https://www.placardefutebol.com.br"
    # Focando no Brasileirão Série A
    response = requests.get(f"{url_base}/brasileirao-serie-a", headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = soup.find_all('a', href=True)
    encontrados = 0

    for link in links:
        if '/jogo/' in link['href']:
            times = link.find_all('span', class_='team-name')
            if len(times) < 2: continue
            
            casa, fora = times[0].text, times[1].text
            prob, status_time = analisar_detalhes(url_base + link['href'])
            
            # Filtro de 50% para ser mais abrangente na análise
            if prob >= 0.5:
                msg = (f"🏟️ *{casa} x {fora}*\n"
                       f"📈 Tendência 1-3 Gols: {prob*100:.0f}%\n"
                       f"📋 Info: {status_time}\n"
                       f"🎯 Sugestão: 1-3 Gols & HT")
                enviar_telegram(msg)
                encontrados += 1
            time.sleep(1)

    if encontrados == 0:
        enviar_telegram("Checking... Nenhum jogo com padrão 1-3 gols detectado para hoje.")

if __name__ == "__main__":
    executar_robo()
    
