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
    enviar_telegram("🕵️ *PodeApostar_Bot:* Varrendo mercados para fechar seu bilhete de 10 jogos...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    # Adicionado 'City' e 'United' para reforçar a lista
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

    # Ajuste: Só envia a mensagem de "Completando" se realmente faltar jogo para chegar em 10
    if len(top_10) >= 10:
        cont_rig = sum(1 for x in top_10 if x['tipo'] == "🥇 RIGOROSO")
        msg = f"📝 *BILHETE FINAL (10 SELEÇÕES):*\n📊 _({cont_rig} Rigorosos encontrados)_\n\n"
        for i, j in enumerate(top_10, 1):
            msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n\n"
        enviar_telegram(msg)
    else:
        # Mostra o número real encontrado antes de completar
        enviar_telegram(f"⚠️ Encontrados {len(top_10)} jogos. Completando bilhete estratégico...")
        completar_bilhete(top_10)

def completar_bilhete(lista_atual):
    # Lista de backup expandida para GARANTIR 10 jogos
    seguranca = [
        {"tipo": "🥇 RIGOROSO", "texto": "Real Madrid x Getafe", "mercado": "Vitória Real"},
        {"tipo": "🥇 RIGOROSO", "texto": "Madureira x Flamengo", "mercado": "Vitória Flamengo"},
        {"tipo": "🥇 RIGOROSO", "texto": "Manchester City x United", "mercado": "Vitória City"},
        {"tipo": "🥇 RIGOROSO", "texto": "Santos x São Bernardo", "mercado": "Vitória Santos"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Bologna x Verona", "mercado": "+1.5 Gols"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Benfica x Portimonense", "mercado": "Vitória Benfica"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Arsenal x Newcastle", "mercado": "+1.5 Gols"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "River Plate x Belgrano", "mercado": "Vitória River"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Inter x Atalanta", "mercado": "Ambas Marcam"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Porto x Estrela Amadora", "mercado": "Vitória Porto"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Bayern x Mainz", "mercado": "Vitória Bayern"},
        {"tipo": "🥈 FLEXÍVEL", "texto": "Palmeiras x Mirassol", "mercado": "Vitória Palmeiras"}
    ]
    
    final = lista_atual
    vistos = {x['texto'].lower() for x in final}
    
    for s in seguranca:
        if len(final) >= 10: break
        if s['texto'].lower() not in vistos:
            final.append(s)
    
    # Re-ordena para garantir os ícones 🥇 no topo da mensagem final
    final.sort(key=lambda x: x['tipo'] == "🥈 FLEXÍVEL")
            
    msg = f"📝 *BILHETE COMPLETO (10 SELEÇÕES):*\n\n"
    for i, j in enumerate(final, 1):
        msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n\n"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
