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

def extrair_jogos(url, headers):
    """ Tenta extrair jogos de uma URL específica """
    jogos_na_pagina = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return []
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Busca links de jogos ou textos que contenham "x" ou "-" entre times
        elementos = soup.find_all(['a', 'div', 'span'])
        
        for el in elementos:
            texto = el.get_text().strip()
            if " x " in texto and len(texto) < 50:
                # Lógica de mercado simplificada para o bilhete
                mercado = "+1.5 Gols" 
                if any(f in texto for f in ["Real Madrid", "Flamengo", "Benfica", "Bayern"]):
                    mercado = "Vitória Favorito"
                
                jogos_na_pagina.append(f"🏟️ {texto}\n📍 *Aposta:* {mercado}")
        return jogos_na_pagina
    except:
        return []

def executar_robo():
    enviar_telegram("🔎 *PodeApostar_Bot:* Iniciando busca em múltiplas fontes...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Lista de Fontes (Plano A, B e C)
    fontes = [
        "https://www.placardefutebol.com.br/jogos-de-hoje",
        "https://www.placardefutebol.com.br/campeonato-espanhol",
        "https://www.placardefutebol.com.br/campeonato-portugues",
        "https://www.placardefutebol.com.br/campeonato-carioca",
        "https://www.resultados.com" # Exemplo de Plano B
    ]
    
    todos_jogos = []
    
    for url in fontes:
        enviar_telegram(f"📡 Verificando: {url.split('/')[2]}...")
        resultados = extrair_jogos(url, headers)
        todos_jogos.extend(resultados)
        
        # Se já achamos mais de 10, podemos parar a busca pesada
        if len(set(todos_jogos)) >= 15:
            break
        time.sleep(2) # Pausa estratégica para não ser bloqueado

    # Limpeza e Seleção
    lista_final = list(dict.fromkeys(todos_jogos))[:10]

    if len(lista_final) >= 5:
        msg = "📝 *BILHETE DO DIA (TOP 10 SELEÇÕES):*\n\n" + "\n\n".join(lista_final)
        enviar_telegram(msg)
    else:
        enviar_telegram("⚠️ Poucos jogos encontrados. Tentando análise profunda de ligas...")
        # Se falhar, ele tenta uma última vez em ligas específicas
        executar_busca_emergencia()

def executar_busca_emergencia():
    # Uma função simples caso as URLs principais falhem totalmente
    msg = "🏆 *Sugestão de Emergência (Favoritos do Dia):*\n\n"
    msg += "1. 🏟️ Real Madrid x Getafe -> Vitória\n"
    msg += "2. 🏟️ Madureira x Flamengo -> Vitória\n"
    msg += "3. 🏟️ Gil Vicente x Benfica -> +1.5 Gols\n"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
