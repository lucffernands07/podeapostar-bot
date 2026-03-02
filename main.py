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
        if total == 0: return None

        # --- CÁLCULOS PARA ODDS BAIXAS (ESTRATÉGIA DE ACÚMULO) ---
        v_casa = sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1]))
        v_fora = sum(1 for p in placares if int(p.split('-')[1]) > int(p.split('-')[0]))
        mais_1_5 = sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2)
        ambas = sum(1 for p in placares if '-' in p and all(int(x) > 0 for x in p.split('-')))

        return {
            "p_casa": (v_casa/total)*100, "p_fora": (v_fora/total)*100,
            "p_gols": (mais_1_5/total)*100, "p_ambas": (ambas/total)*100,
            "total": total
        }
    except: return None

def executar_robo():
    enviar_telegram("🎯 *PodeApostar_Bot:* Buscando bases para sua Super Múltipla...")
    
    url_base = "https://www.placardefutebol.com.br"
    ligas = [
        "/brasileirao-serie-a", "/campeonato-paulista", "/campeonato-carioca",
        "/campeonato-ingles", "/campeonato-italiano", "/campeonato-espanhol", 
        "/campeonato-portugues", "/campeonato-argentino"
    ]
    
    total_avisos = 0
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
                        # BAIXAMOS A RÉGUA: Se tiver 35% de chance de vitória ou 50% de gols, ele já avisa.
                        # Isso garante que os favoritos de odd 1.30 (como o Flamengo) apareçam.
                        dicas = []
                        if res["p_casa"] >= 35: dicas.append(f"🏆 Vitória {times[0].text} ({res['p_casa']:.0f}%)")
                        if res["p_fora"] >= 35: dicas.append(f"🏆 Vitória {times[1].text} ({res['p_fora']:.0f}%)")
                        if res["p_gols"] >= 50: dicas.append(f"⚽ +1.5 Gols ({res['p_gols']:.0f}%)")
                        if res["p_ambas"] >= 40: dicas.append(f"🔄 Ambas Marcam ({res['p_ambas']:.0f}%)")
                        
                        if dicas:
                            msg = f"🏟️ *{times[0].text} x {times[1].text}*\n" + "\n".join(dicas)
                            enviar_telegram(msg)
                            total_avisos += 1
                        time.sleep(1)
        except: continue

if __name__ == "__main__":
    executar_robo()
