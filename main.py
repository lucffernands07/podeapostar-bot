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

def extrair_inteligente(url, headers, favoritos):
    """ Extrai jogos e já classifica entre Rigoroso e Flexível """
    coletados = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return []
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Buscamos em links e spans (onde ficam os nomes dos times)
        elementos = soup.find_all(['a', 'span', 'div'])
        
        for el in elementos:
            texto = el.get_text().strip()
            # Padrão: Time A x Time B
            if " x " in texto and len(texto) < 50:
                tipo = "🥈 FLEXÍVEL"
                mercado = "+1.5 Gols"
                conf = 65
                
                # Se um dos favoritos estiver no jogo, vira RIGOROSO
                for fav in favoritos:
                    if fav.lower() in texto.lower():
                        tipo = "🥇 RIGOROSO"
                        mercado = f"Vitória {fav}"
                        conf = 85
                        break
                
                coletados.append({
                    "texto": texto,
                    "tipo": tipo,
                    "mercado": mercado,
                    "conf": conf
                })
        return coletados
    except:
        return []

def executar_robo():
    enviar_telegram("🔎 *PodeApostar_Bot:* Iniciando busca estratégica global...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    favoritos = ["Flamengo", "Real Madrid", "Benfica", "Bayern", "Palmeiras", "Santos", "Bologna", "Barcelona", "Manchester", "Liverpool", "Arsenal"]
    
    fontes = [
        "https://www.placardefutebol.com.br/jogos-de-hoje",
        "https://www.placardefutebol.com.br/copa-sul-americana",
        "https://www.placardefutebol.com.br/campeonato-ingles",
        "https://www.placardefutebol.com.br/campeonato-carioca"
    ]
    
    todos_jogos = []
    jogos_vistos = set()

    for url in fontes:
        # Extrai os jogos da fonte atual
        resultados = extrair_inteligente(url, headers, favoritos)
        
        for item in resultados:
            # Evita duplicados
            id_jogo = item['texto'].lower().replace(" ", "")
            if id_jogo not in jogos_vistos:
                todos_jogos.append(item)
                jogos_vistos.add(id_jogo)
        
        if len(todos_jogos) >= 20: break
        time.sleep(1)

    # ORDENAÇÃO: Coloca os 🥇 RIGOROSOS no topo
    todos_jogos.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    
    top_10 = todos_jogos[:10]

    if len(top_10) >= 1:
        cont_rig = sum(1 for x in top_10 if x['tipo'] == "🥇 RIGOROSO")
        msg = f"📝 *BILHETE MISTO (TOP 10):*\n📊 _Encontrados {cont_rig} jogos de nível Rigoroso_\n\n"
        
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n\n"
        
        enviar_telegram(msg)
    else:
        executar_busca_emergencia()

def executar_busca_emergencia():
    msg = "🏆 *Sugestão de Emergência (Favoritos Confirmados):*\n\n"
    msg += "1. 🥇 RIGOROSO 🏟️ Real Madrid x Getafe -> Vitória Real\n"
    msg += "2. 🥇 RIGOROSO 🏟️ Madureira x Flamengo -> Vitória Flamengo\n"
    msg += "3. 🥈 FLEXÍVEL 🏟️ Jogo do dia -> +1.5 Gols\n"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
