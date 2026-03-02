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

        # Cálculos de probabilidade baseados no histórico
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
    enviar_telegram("🚀 *PodeApostar_Bot:* Iniciando análise para Múltiplas (BRA, ESP, POR, ARG, ITA)...")
    
    url_base = "https://www.placardefutebol.com.br"
    # Lista de ligas atualizada conforme seu pedido
    ligas = [
        "/brasileirao-serie-a", 
        "/campeonato-paulista", 
        "/campeonato-carioca",
        "/campeonato-ingles", 
        "/campeonato-italiano", 
        "/campeonato-espanhol", 
        "/campeonato-portugues", 
        "/campeonato-argentino"
    ]
    
    total_avisos = 0
    for liga in ligas:
        try:
            response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) < 2: continue
                    
                    time_a, time_b = times[0].text, times[1].text
                    res = analisar_detalhes(url_base + link['href'])
                    
                    if res:
                        # Filtro de 45% para garantir volume na múltipla
                        msg = f"🏟️ *{time_a} x {time_b}*\n"
                        dicas = []
                        if res["p_casa"] >= 45: dicas.append(f"✅ Vitória {time_a} ({res['p_casa']:.0f}%)")
                        if res["p_fora"] >= 45: dicas.append(f"✅ Vitória {time_b} ({res['p_fora']:.0f}%)")
                        if res["p_gols"] >= 60: dicas.append(f"⚽ Mínimo 2 Gols ({res['p_gols']:.0f}%)")
                        if res["p_ambas"] >= 45: dicas.append(f"🔄 Ambas Marcam ({res['p_ambas']:.0f}%)")
                        
                        if dicas:
                            msg += "\n".join(dicas) + f"\n📊 _Base: {res['total']} jogos_"
                            enviar_telegram(msg)
                            total_avisos += 1
                        time.sleep(1)
        except: continue

    if total_avisos == 0:
        enviar_telegram("⚠️ Nenhum padrão encontrado nas ligas selecionadas agora.")

if __name__ == "__main__":
    executar_robo()
