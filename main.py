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
        for el in soup.find_all(['a', 'span', 'div']):
            texto = el.get_text().strip() if not el.get('title') else el.get('title').strip()
            
            # FILTRO: Precisa ser jogo (x) e NÃO pode ter data (/) no texto
            if " x " in texto and 5 < len(texto) < 60:
                if "/" in texto: # Se tiver data (ex: 10/03), ignora pois não é hoje
                    continue
                
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Lista de elite para classificar os jogos encontrados HOJE
    favoritos = ["Flamengo", "Real Madrid", "Benfica", "Bayern", "Palmeiras", "Santos", "Bologna", "Barcelona", "City", "Liverpool", "Arsenal", "Inter", "Milan", "Porto", "River Plate", "United"]
    
    # Foco total na página de HOJE para evitar rodadas futuras
    fontes = ["https://www.placardefutebol.com.br/jogos-de-hoje"]
    
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

    # Ordena: Rigorosos primeiro, depois por Confiança
    todos_jogos.sort(key=lambda x: (x['tipo'] == "🥈 FLEXÍVEL", -x['conf']))
    
    # Pega o que encontrou (máximo 10)
    final = todos_jogos[:10]

    if len(final) > 0:
        msg = "📝 *BILHETE DO DIA (RODADA DE HOJE):*\n\n"
        for i, j in enumerate(final, 1):
            msg += f"{i}. {j['tipo']} 🏟️ {j['texto']}\n📍 *Aposta:* {j['mercado']}\n📈 *Confiança:* {j['conf']}%\n\n"
        enviar_telegram(msg)
    else:
        # Se não tiver NADA hoje, ele avisa em vez de mandar lixo
        enviar_telegram("⚠️ *Aviso:* Nenhum jogo de elite detectado para a rodada de hoje.")

if __name__ == "__main__":
    executar_robo()
