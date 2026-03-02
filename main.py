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
        
        # Se não tiver histórico, tentamos prever com base nos últimos jogos gerais
        if total == 0: return {"prob": 50, "mercado": "Tendência de Gols"}

        v_casa = (sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1])) / total) * 100
        v_fora = (sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0])) / total) * 100
        mais_1_5 = (sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2) / total) * 100
        ambas = (sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-'))) / total) * 100

        opcoes = [(v_casa, "Vencer"), (v_fora, "Vencer"), (mais_1_5, "+1.5 Gols"), (ambas, "Ambas Marcam")]
        prob, mercado = max(opcoes)
        return {"prob": prob, "mercado": mercado}
    except: return None

def executar_robo():
    enviar_telegram("⚡ *PodeApostar_Bot:* Gerando bilhete agora...")
    url_base = "https://www.placardefutebol.com.br"
    ligas = ["/brasileirao-serie-a", "/campeonato-paulista", "/campeonato-carioca", "/copa-sul-americana", 
             "/campeonato-ingles", "/campeonato-italiano", "/campeonato-espanhol", "/campeonato-portugues", "/campeonato-argentino"]
    
    jogos = []
    for liga in ligas:
        try:
            res_liga = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup_liga = BeautifulSoup(res_liga.text, 'html.parser')
            for link in soup_liga.find_all('a', href=True):
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) >= 2:
                        dados = analisar_detalhes(url_base + link['href'])
                        if dados:
                            jogos.append({"nome": f"{times[0].text} x {times[1].text}", "mercado": dados["mercado"], "prob": dados["prob"]})
                if len(jogos) >= 20: break # Limite de busca para ser rápido
        except: continue

    jogos.sort(key=lambda x: x['prob'], reverse=True)
    top_10 = jogos[:10]

    if top_10:
        msg = "📝 *BILHETE DO DIA (10 JOGOS):*\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {j['nome']}\n📍 *Aposta:* {j['mercado']}\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("❌ Erro ao coletar jogos. Verifique os links das ligas.")

if __name__ == "__main__":
    executar_robo()
