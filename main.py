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

        # Cálculos de Probabilidade
        v_casa = (sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1])) / total) * 100
        v_fora = (sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0])) / total) * 100
        mais_1_5 = (sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2) / total) * 100
        ambas = (sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-'))) / total) * 100
        zero_gols = (sum(1 for p in placares if sum(map(int, p.split('-'))) == 0) / total) * 100

        # Encontra a melhor opção estatística deste jogo específico
        opcoes = [
            (v_casa, "Vitória Casa"),
            (v_fora, "Vitória Fora"),
            (mais_1_5, "Mais de 1.5 Gols"),
            (ambas, "Ambas Marcam: Sim"),
            (zero_gols, "Menos de 0.5 Gols (0-0)")
        ]
        melhor_valor, mercado = max(opcoes)
        return {"prob": melhor_valor, "mercado": mercado}
    except: return None

def executar_robo():
    enviar_telegram("🎯 *PodeApostar_Bot:* Selecionando os 10 Melhores para sua Super Múltipla...")
    url_base = "https://www.placardefutebol.com.br"
    ligas = ["/brasileirao-serie-a", "/campeonato-paulista", "/campeonato-carioca", 
             "/campeonato-ingles", "/campeonato-italiano", "/campeonato-espanhol", 
             "/campeonato-portugues", "/campeonato-argentino"]
    
    lista_final = []

    for liga in ligas:
        response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if '/jogo/' in link['href']:
                times = link.find_all('span', class_='team-name')
                if len(times) < 2: continue
                
                res = analisar_detalhes(url_base + link['href'])
                if res:
                    lista_final.append({
                        "jogo": f"{times[0].text} x {times[1].text}",
                        "prob": res["prob"],
                        "mercado": res["mercado"]
                    })
                time.sleep(0.5)

    # ORDENAÇÃO INTELIGENTE: Pega os 10 jogos com as MAIORES probabilidades do dia
    lista_final.sort(key=lambda x: x['prob'], reverse=True)
    top_10 = lista_final[:10]

    if top_10:
        msg = "📝 *SEU BILHETE DE HOJE (TOP 10):*\n\n"
        for i, item in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {item['jogo']}\n📍 *Aposta:* {item['mercado']} ({item['prob']:.0f}%)\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("🔍 Não encontrei jogos suficientes com dados para o Top 10.")

if __name__ == "__main__":
    executar_robo()
