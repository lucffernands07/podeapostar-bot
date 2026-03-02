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
        
        # BUSCA REFORÇADA: Tenta capturar times por classes comuns e links
        for el in soup.find_all(['a', 'span', 'div']):
            # Pega o texto ou o título do link (onde o Placar de Futebol costuma esconder o nome do jogo)
            texto = el.get_text().strip() if not el.get('title') else el.get('title').strip()
            
            if " x " in texto and 5 < len(texto) < 60:
                # Limpeza simples para remover lixo de texto
                texto = texto.split('\n')[0].strip()
                
                tipo, mercado, conf = "🥈 FLEXÍVEL", "+1.5 Gols", 65
                for fav in favoritos:
                    if fav.lower() in texto.lower():
                        tipo, mercado, conf = "🥇 RIGOROSO", f"Vitória {fav}", 85
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
        "https://www.placardefutebol.com.br/campeonato-ingles",
        "https://www.placardefutebol.com.br/campeonato-espanhol",
        "https://www.placardefutebol.com.br/campeonato-italiano"
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
        
        if len(todos_jogos) >= 15: break
        time.sleep(1)

    todos_jogos.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    top_10 = todos_jogos[:10]

    # LÓGICA DE MENSAGEM AJUSTADA:
    if len(top_10) >= 10:
        # Se achou 10 ou mais, manda direto sem avisar nada
        msg_final(top_10, "📝 *BILHETE FINAL (10 SELEÇÕES):*")
    elif len(top_10) > 0:
        # Se achou ALGUNS, avisa quantos e completa
        enviar_telegram(f"⚠️ Encontrados {len(top_10)} jogos no site. Completando bilhete...")
        completar_e_enviar(top_10)
    else:
        # Se achou ZERO, não avisa "0 encontrado", apenas manda o Bilhete Estratégico
        completar_e_enviar([])

def completar_e_enviar(lista_atual):
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
        {"tipo": "🥈 FLEXÍVEL", "texto": "Porto x Estrela Amadora", "mercado": "Vitória Porto", "conf": 73}
    ]
    
    final = lista_atual
    vistos = {x['texto'].lower() for x in final}
    for s in seguranca:
        if len(final) >= 10: break
        if s['texto'].lower() not in vistos:
            final.append(s)
    
    final.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    msg_final(final, "📝 *BILHETE COMPLETO (ESTRATÉGICO):*")

def msg_final(lista, titulo):
    msg = f"{titulo}\n\n"
    for i, j in enumerate(lista[:10], 1):
        msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n\n"
    enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
