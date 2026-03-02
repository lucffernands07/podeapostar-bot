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
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total = len(placares)
        if total < 3: return None

        # --- CÁLCULO DE PROBABILIDADES ---
        vitoria_casa = sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1]))
        vitoria_fora = sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0]))
        mais_1_5 = sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2)
        ambas_sim = sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-')))

        return {
            "casa": (vitoria_casa / total) * 100,
            "fora": (vitoria_fora / total) * 100,
            "gols": (mais_1_5 / total) * 100,
            "ambas": (ambas_sim / total) * 100,
            "total": total
        }
    except: return None

def executar_robo():
    enviar_telegram("📊 *PodeApostar_Bot:* Caçando Melhores Mercados para Múltipla...")
    url_base = "https://www.placardefutebol.com.br"
    # Ligas da sua print: Carioca (Flamengo), Argentina, Europa
    ligas = ["/campeonato-carioca", "/campeonato-ingles", "/campeonato-italiano", 
             "/campeonato-espanhol", "/campeonato-portugues", "/campeonato-argentino"]
    
    for liga in ligas:
        response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if '/jogo/' in link['href']:
                times = link.find_all('span', class_='team-name')
                if len(times) < 2: continue
                
                res = analisar_detalhes(url_base + link['href'])
                if res:
                    time_a, time_b = times[0].text, times[1].text
                    sugestao = ""
                    
                    # --- LÓGICA DE DECISÃO DA ESTRATÉGIA ---
                    # 1. Se um time vence muito (ex: Flamengo ou Real Madrid)
                    if res["casa"] >= 60: sugestao = f"🏆 *Vitória:* {time_a}"
                    elif res["fora"] >= 60: sugestao = f"🏆 *Vitória:* {time_b}"
                    
                    # 2. Se o Ambas Marcam é muito forte (ex: Fiorentina ou Benfica)
                    elif res["ambas"] >= 55: sugestao = "🔄 *Ambas Marcam: SIM*"
                    
                    # 3. Se o foco for apenas 2 gols na partida (Over 1.5)
                    elif res["gols"] >= 70: sugestao = "⚽ *Mínimo 2 Gols na partida*"

                    if sugestao:
                        msg = (f"🏟️ *{time_a} x {time_b}*\n"
                               f"📍 {sugestao}\n"
                               f"📈 Confiança: {max(res['casa'], res['fora'], res['ambas'], res['gols']):.0f}%\n"
                               f"📚 Histórico: {res['total']} jogos")
                        enviar_telegram(msg)
                time.sleep(1)

if __name__ == "__main__":
    executar_robo()
