import os
import requests
from bs4 import BeautifulSoup
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try: requests.get(url)
    except: pass

def analisar_detalhes(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        texto_pagina = soup.get_text().lower()

        # Status de Escalação
        status = "✅ Titulares Prováveis"
        if any(w in texto_pagina for w in ["reserva", "poupado", "desfalques", "injury"]):
            status = "⚠️ Atenção: Possíveis Reservas"

        # Coleta de placares históricos (H2H)
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total = len(placares)
        if total == 0: return None

        # Contagem de cenários
        zero_gols = sum(1 for p in placares if sum(map(int, p.split('-'))) == 0)
        exato_1 = sum(1 for p in placares if sum(map(int, p.split('-'))) == 1)
        exato_2 = sum(1 for p in placares if sum(map(int, p.split('-'))) == 2)
        tres_ou_mais = sum(1 for p in placares if sum(map(int, p.split('-'))) >= 3)

        return {
            "0_gols": (zero_gols / total),
            "1_gol": (exato_1 / total),
            "2_gols": (exato_2 / total),
            "3_mais": (tres_ou_mais / total),
            "status": status
        }
    except: return None

def executar_robo():
    enviar_telegram("🎯 *PodeApostar_Bot:* Varredura Multi-Alertas Iniciada!")
    url_base = "https://www.placardefutebol.com.br"
    ligas = ["/brasileirao-serie-a", "/campeonato-ingles", "/campeonato-italiano", 
             "/campeonato-espanhol", "/campeonato-portugues", "/campeonato-argentino"]
    
    total_encontrados = 0

    for liga in ligas:
        response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if '/jogo/' in link['href']:
                times = link.find_all('span', class_='team-name')
                if len(times) < 2: continue
                
                res = analisar_detalhes(url_base + link['href'])
                if not res: continue

                # Lógica de Alertas Separados (Foco em Odd ~1.40)
                # Se a probabilidade é > 40%, a estatística justifica a entrada
                alertas = []
                if res["0_gols"] > 0.40: alertas.append("🚫 *Alerta:* Tendência 0 Gols (Under 0.5)")
                if res["1_gol"] > 0.40:  alertas.append("⚽ *Alerta:* Tendência 1 Gol Exato")
                if res["2_gols"] > 0.40: alertas.append("✌️ *Alerta:* Tendência 2 Gols Exatos")
                if res["3_mais"] > 0.40: alertas.append("🔥 *Alerta:* Tendência 3+ Gols (Over 2.5)")
                
                # Alerta para sua estratégia de Mínimo 2 Gols (Over 1.5)
                if (res["2_gols"] + res["3_mais"]) > 0.50:
                    alertas.append("🚀 *ESTRATÉGIA:* Mínimo 2 Gols (Over 1.5)")

                if alertas:
                    msg = (f"🏆 *{liga.replace('/','').upper()}*\n"
                           f"🏟️ {times[0].text} x {times[1].text}\n"
                           f"📋 {res['status']}\n"
                           + "\n".join(alertas))
                    enviar_telegram(msg)
                    total_encontrados += 1
                time.sleep(1)

    if total_encontrados == 0:
        enviar_telegram("🔍 Sem jogos com padrões de odds mínimas para hoje.")

if __name__ == "__main__":
    executar_robo()
                
