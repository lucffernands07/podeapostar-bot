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
    coletados = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return []
        
        soup = BeautifulSoup(res.text, 'html.parser')
        for el in soup.find_all(['a', 'span', 'div', 'p']):
            texto = el.get_text().strip()
            if " x " in texto and 5 < len(texto) < 60 and '\n' not in texto:
                tipo = "🥈 FLEXÍVEL"
                mercado = "+1.5 Gols"
                conf = 65
                
                for fav in favoritos:
                    if fav.lower() in texto.lower():
                        tipo = "🥇 RIGOROSO"
                        mercado = f"Vitória {fav}"
                        conf = 85
                        break
                
                coletados.append({"texto": texto, "tipo": tipo, "mercado": mercado, "conf": conf})
        return coletados
    except:
        return []

def executar_robo():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    favoritos = ["Flamengo", "Real Madrid", "Benfica", "Bayern", "Palmeiras", "Santos", "Bologna", "Barcelona", "Manchester", "City", "Liverpool", "Arsenal", "Inter", "Milan", "Porto", "River Plate", "United"]
    
    fontes = [
        "https://www.placardefutebol.com.br/jogos-de-hoje",
        "https://www.placardefutebol.com.br/copa-sul-americana",
        "https://www.placardefutebol.com.br/campeonato-ingles",
        "https://www.placardefutebol.com.br/campeonato-espanhol",
        "https://www.placardefutebol.com.br/campeonato-italiano",
        "https://www.placardefutebol.com.br/campeonato-carioca",
        "https://www.placardefutebol.com.br/campeonato-paulista"
    ]
    
    todos_jogos = []
    jogos_vistos = set()

    for url in fontes:
        resultados = extrair_inteligente(url, headers, favoritos)
        for item in resultados:
            id_jogo = item['texto'].lower().replace(" ", "")
            if id_jogo not in jogos_vistos:
                todos_jogos.append(item)
                jogos_vistos.add(id_jogo)
        
        if len(todos_jogos) >= 15:
            break
        time.sleep(1)

    todos_jogos.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    top_10 = todos_jogos[:10]

    if len(top_10) >= 10:
        cont_rig = sum(1 for x in top_10 if x['tipo'] == "🥇 RIGOROSO")
        msg = f"📝 *BILHETE FINAL (10 SELEÇÕES):*\n📊 _({cont_rig} Rigorosos encontrados)_\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n\n"
        enviar_telegram(msg)
    else:
        # Só avisa se realmente encontrou menos que 10
        enviar_telegram(f"⚠️ Encontrados {len(top_10)} jogos no site. Completando bilhete estratégico...")
        completar_bilhete(top_10)

def completar_bilhete(lista_atual):
    seguranca = [
        {"tipo": "🥇 RIGOROSO", "texto": "Real Madrid x Getafe", "mercado": "Vitória Real", "conf": 88},
        {"tipo": "🥇 RIGOROSO", "texto": "Madureira x Flamengo", "mercado": "Vitória Flamengo", "conf": 85},
        {"tipo": "🥇 RIGOROSO", "texto": "Manchester City x United", "mercado": "Vitória City", "conf": 82},
        {"tipo": "🥇 RIGOROSO", "texto": "Santos x São Bernardo", "mercado": "Vitória Santos", "conf": 80},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Bologna x Verona", "mercado": "+1.5 Gols", "conf": 72},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Benfica x Portimonense", "mercado": "Vitória Benfica", "conf": 75},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Arsenal x Newcastle", "mercado": "+1.5 Gols", "conf": 70},
        {"tipo": "🥈 FLEXÍVEL", "texto": "River Plate x Belgrano", "mercado": "Vitória River", "conf": 74},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Inter x Atalanta", "mercado": "Ambas Marcam", "conf": 68},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Porto x Estrela Amadora", "mercado": "Vitória Porto", "conf": 73},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Bayern x Mainz", "mercado": "Vitória Bayern", "conf": 78},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Palmeiras x Mirassol", "mercado": "Vitória Palmeiras", "conf": 77}
    ]
    
    final = lista_atual
    vistos = {x['texto'].lower() for x in final}
    
    for s in seguranca:
        if len(final) >= 10: break
        if s['texto'].lower() not in vistos:
            final.append(s)
    
    final.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
            
    msg = f"📝 *BILHETE COMPLETO (10 SELEÇÕES):*\n\n"
    for i, j in enumerate(final, 1):
        msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n\n"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
