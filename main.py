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

def analisar_jogo(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total = len(placares)
        
        # --- LÓGICA RIGOROSA (Com Histórico) ---
        if total >= 2:
            v_casa = (sum(1 for p in placares if int(p.split('-')[0]) > int(p.split('-')[1])) / total) * 100
            mais_1_5 = (sum(1 for p in placares if sum(map(int, p.split('-'))) >= 2) / total) * 100
            
            prob, merc = (v_casa, "Vitória Casa") if v_casa > mais_1_5 else (mais_1_5, "Mais de 1.5 Gols")
            if prob >= 75:
                return {"tipo": "🥇 RIGOROSO", "conf": prob, "mercado": merc}
        
        # --- LÓGICA FLEXÍVEL (Tendência) ---
        return {"tipo": "🥈 FLEXÍVEL", "conf": 65, "mercado": "+1.5 Gols (Tendência)"}
    except:
        return None

def executar_robo():
    enviar_telegram("🕵️ *Analisando Ligas:* Buscando apostas Rigorosas e Flexíveis...")
    url_base = "https://www.placardefutebol.com.br"
    ligas = ["/campeonato-espanhol", "/campeonato-portugues", "/campeonato-carioca", "/campeonato-paulista", "/brasileirao-serie-a", "/copa-sul-americana", "/campeonato-argentino"]
    
    lista_final = []
    for liga in ligas:
        try:
            res_l = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup_l = BeautifulSoup(res_l.text, 'html.parser')
            for link in soup_l.find_all('a', href=True):
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) >= 2:
                        analise = analisar_jogo(url_base + link['href'])
                        if analise:
                            lista_final.append({
                                "jogo": f"{times[0].text} x {times[1].text}",
                                "tipo": analise["tipo"],
                                "mercado": analise["mercado"],
                                "conf": analise["conf"]
                            })
            time.sleep(1)
        except: continue

    # ORDENAÇÃO: Prioriza os Rigorosos (🥇) e depois por Confiança
    lista_final.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    top_10 = lista_final[:10]

    if top_10:
        cont_rig = sum(1 for x in top_10 if x['tipo'] == "🥇 RIGOROSO")
        msg = f"📝 *BILHETE MISTO (TOP 10):*\n📊 _Encontrados {cont_rig} jogos Rigorosos_\n\n"
        for i, item in enumerate(top_10, 1):
            msg += f"{i}. {item['tipo']} 🏟️ {item['jogo']}\n📍 *Aposta:* {item['mercado']} ({item['conf']:.0f}%)\n\n"
        enviar_telegram(msg)
    else:
        enviar_telegram("❌ Nenhum jogo encontrado nas ligas selecionadas.")

if __name__ == "__main__":
    executar_robo()
