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
        # Varre o site em busca de jogos reais da página "Jogos de Hoje"
        for el in soup.find_all(['a', 'span', 'div']):
            texto = el.get_text().strip() if not el.get('title') else el.get('title').strip()
            
            # Filtro rigoroso: Tem que ter " x " e não pode ter data (/) nem "Ontem"
            if " x " in texto and 5 < len(texto) < 60:
                if "/" in texto or "Ontem" in texto: 
                    continue
                
                # Limpa o texto de possíveis sobras de HTML
                texto = texto.split('\n')[0].strip()
                
                tipo, mercado, conf = "🥈 FLEXÍVEL", "+1.5 Gols", 65
                
                # Se o time favorito está no jogo DE HOJE, vira Rigoroso
                for fav in favoritos:
                    if fav.lower() in texto.lower():
                        tipo, mercado, conf = "🥇 RIGOROSO", f"Vitória {fav}", 85
                        break
                
                coletados.append({"texto": texto, "tipo": tipo, "mercado": mercado, "conf": conf})
        return coletados
    except:
        return []

def executar_robo():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Nossa lista de elite serve apenas para conferir se os times jogam HOJE
    favoritos = ["Flamengo", "Real Madrid", "Benfica", "Bayern", "Palmeiras", "Santos", "Bologna", "Barcelona", "City", "Liverpool", "Arsenal", "Inter", "Milan", "Porto", "River Plate", "United"]
    
    # URL ÚNICA: Apenas o que entra em campo hoje
    fontes = ["https://www.placardefutebol.com.br/jogos-de-hoje"]
    
    todos_jogos = []
    jogos_vistos = set()

    for url in fontes:
        resultados = extrair_inteligente(url, headers, favoritos)
        for item in resultados:
            # Evita duplicados
            id_jogo = item['texto'].lower().replace(" ", "")
            if id_jogo not in jogos_vistos:
                todos_jogos.append(item)
                jogos_vistos.add(id_jogo)

    # Ordena: Rigorosos primeiro, depois por Confiança
    todos_jogos.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    
    # Pega o máximo que encontrar (até 10)
    final = todos_jogos[:10]

    if len(final) > 0:
        msg = "📝 *BILHETE REAL (RODADA DE HOJE):*\n"
        msg += f"📊 _Encontrados {len(final)} jogos confirmados_\n\n"
        for i, j in enumerate(final, 1):
            msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n\n"
        enviar_telegram(msg)
    else:
        # Se não tiver jogo hoje, ele não inventa!
        enviar_telegram("⚠️ *Aviso:* Nenhum jogo relevante encontrado para a data de hoje.")

if __name__ == "__main__":
    executar_robo()
    
