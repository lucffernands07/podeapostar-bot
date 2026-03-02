import os
import requests
from bs4 import BeautifulSoup
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    requests.get(url)

def analisar_historico(url_jogo):
    """Entra no link do jogo e analisa os últimos resultados"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Aqui o robô busca os placares (ex: '2-1', '1-0')
        # Esta parte simula a captura de dados de gols
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        
        gols_no_range = 0
        total_jogos = len(placares)
        
        for placar in placares:
            try:
                gols = sum(map(int, placar.split('-')))
                if 1 <= gols <= 3:
                    gols_no_range += 1
            except:
                continue
        
        # Retorna a porcentagem de jogos que ficaram entre 1 e 3 gols
        return (gols_no_range / total_jogos) if total_jogos > 0 else 0
    except:
        return 0

def executar_robo():
    enviar_telegram("🚀 *PodeApostar_Bot:* Iniciando análise profunda da rodada...")
    
    url_base = "https://www.placardefutebol.com.br"
    url_serie_a = f"{url_base}/brasileirao-serie-a"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url_serie_a, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links_jogos = soup.find_all('a', href=True)
    jogos_analisados = 0

    for link in links_jogos:
        if '/jogo/' in link['href']:
            url_final = url_base + link['href']
            # O robô "entra" no jogo para analisar
            print(f"Analisando: {url_final}")
            
            # Pegamos os nomes dos times
            times = link.find_all('span', class_='team-name')
            if len(times) < 2: continue
            
            casa, fora = times[0].text, times[1].text
            
            # Chama a função de inteligência
            probabilidade = analisar_historico(url_final)
            
            # SE A PROBABILIDADE FOR MAIOR QUE 70%, MANDA O ALERTA
            if probabilidade >= 0.7:
                msg = (f"✅ *OPORTUNIDADE DETECTADA*\n"
                       f"🏟️ {casa} x {fora}\n"
                       f"📈 Tendência 1-3 Gols: {probabilidade*100:.0f}%\n"
                       f"🔥 Dica: Entrar em 1-3 Gols e Over 0.5 HT")
                enviar_telegram(msg)
                jogos_analisados += 1
            
            time.sleep(1) # Pausa para não ser bloqueado pelo site

    if jogos_analisados == 0:
        enviar_telegram("Checking... Nenhum jogo com 70%+ de tendência encontrado hoje.")

if __name__ == "__main__":
    executar_robo()
    
