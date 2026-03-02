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
        if total < 2: return None

        # Cálculos de Probabilidade (Sensibilidade aumentada)
        v_casa = (sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1])) / total) * 100
        v_fora = (sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0])) / total) * 100
        mais_1_5 = (sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2) / total) * 100
        ambas = (sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-'))) / total) * 100

        opcoes = [
            (v_casa, "Vitória Casa"),
            (v_fora, "Vitória Fora"),
            (mais_1_5, "Mínimo 2 Gols"),
            (ambas, "Ambas Marcam")
        ]
        
        # Pega a melhor opção do jogo
        prob, mercado = max(opcoes)
        return {"prob": prob, "mercado": mercado}
    except: return None

def executar_robo():
    enviar_telegram("📡 *PodeApostar_Bot:* Gerando Bilhete Top 10 (Sula incluída)...")
    url_base = "https://www.placardefutebol.com.br"
    
    # Lista de Ligas com Sula e Brasileiros
    ligas = [
        "/brasileirao-serie-a", "/campeonato-paulista", "/campeonato-carioca",
        "/copa-sul-americana", "/campeonato-ingles", "/campeonato-italiano",
        "/campeonato-espanhol", "/campeonato-portugues", "/campeonato-argentino"
    ]
    
    jogos_encontrados = []

    for liga in ligas:
        try:
            response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) < 2: continue
                    
                    res = analisar_detalhes(url_base + link['href'])
                    if res:
                        jogos_encontrados.append({
                            "nome": f"{times[0].text} x {times[1].text}",
                            "prob": res["prob"],
                            "mercado": res["mercado"]
                        })
                    time.sleep(0.3)
        except: continue

    # Ordena do mais provável para o menos e pega os 10 melhores
    jogos_encontrados.sort(key=lambda x: x['prob'], reverse=True)
    top_10 = jogos_encontrados[:10]

    if top_10:
        msg = "📝 *BILHETE SUGERIDO (TOP 10):*\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {j['nome']}\n📍 *Aposta:* {j['mercado']} ({j['prob']:.0f}%)\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("🔍 Ainda buscando dados suficientes para o Top 10.")

if __name__ == "__main__":
    executar_robo()
