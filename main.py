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

def analisar_probabilidades(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total = len(placares)
        
        if total < 2: return None # Ignora jogos sem histórico suficiente

        # Cálculo Real de Tendência
        v_casa = (sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1])) / total) * 100
        v_fora = (sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0])) / total) * 100
        mais_1_5 = (sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2) / total) * 100
        ambas = (sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-'))) / total) * 100

        # Identifica o mercado com maior probabilidade neste jogo
        opcoes = [
            (v_casa, "Vitória Casa"),
            (v_fora, "Vitória Fora"),
            (mais_1_5, "Mais de 1.5 Gols"),
            (ambas, "Ambas Marcam")
        ]
        
        prob_max, mercado_eleito = max(opcoes)
        return {"confianca": prob_max, "mercado": mercado_eleito}
    except:
        return None

def executar_robo():
    enviar_telegram("🧠 *Estrategista_Bot:* Analisando o mundo para encontrar o Top 10...")
    
    url_base = "https://www.placardefutebol.com.br"
    ligas = [
        "/campeonato-espanhol", "/campeonato-ingles", "/campeonato-italiano", 
        "/campeonato-portugues", "/campeonato-alemao", "/campeonato-frances",
        "/campeonato-carioca", "/campeonato-paulista", "/brasileirao-serie-a", 
        "/campeonato-argentino", "/copa-sul-americana", "/campeonato-holandes"
    ]
    
    banco_de_dados = []
    jogos_vistos = set()

    for liga in ligas:
        try:
            res = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) >= 2:
                        nome_jogo = f"{times[0].text} x {times[1].text}"
                        if nome_jogo not in jogos_vistos:
                            analise = analisar_probabilidades(url_base + link['href'])
                            if analise:
                                banco_de_dados.append({
                                    "jogo": nome_jogo,
                                    "mercado": analise["mercado"],
                                    "confianca": analise["confianca"]
                                })
                                jogos_vistos.add(nome_jogo)
            time.sleep(0.5)
        except: continue

    # ESTRATÉGIA: Ordenar do maior para o menor (Ranking de Confiança)
    banco_de_dados.sort(key=lambda x: x['confianca'], reverse=True)
    top_10 = banco_de_dados[:10]

    if top_10:
        msg = "🏆 *TOP 10 MELHORES APOSTAS DO MUNDO (HOJE):*\n\n"
        for i, item in enumerate(top_10, 1):
            msg += f"{i}. 🏟️ {item['jogo']}\n📍 *Aposta:* {item['mercado']}\n📈 *Confiança:* {item['confianca']:.0f}%\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("❌ Dados insuficientes para montar o Top 10 estratégico hoje.")

if __name__ == "__main__":
    executar_robo()
