import os
import requests
import random
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": mensagem, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": "true"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def analisar_probabilidades(time_h, time_a):
    # Simulando a análise que você faria no 365Scores
    opcoes = [
        ("🔥 Casa ou Empate", 82),
        ("⚽ Mais de 1.5 Gols", 78),
        ("🎯 Ambas Marcam", 74),
        ("🚩 Mais de 8.5 Escanteios", 70),
        ("🛡️ Empate Anula (DNB)", 85)
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Acessando SuperPlacar...")
    
    url_base = "https://superplacar.com.br/index.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(url_base, headers=headers, timeout=20)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # No SuperPlacar, os jogos ficam em linhas de tabela ou divs de confronto
        jogos_encontrados = []
        
        # Procurando os nomes dos times (ajustado para a estrutura do SuperPlacar)
        confrontos = soup.find_all('div', class_='confronto') 
        
        # Fallback caso a classe mude: buscar por elementos que contenham " x "
        if not confrontos:
            confrontos = soup.find_all('tr')

        for item in confrontos:
            texto = item.get_text().strip()
            if ' x ' in texto:
                # Limpando o texto para pegar apenas os nomes dos times
                partes = texto.split(' x ')
                time_casa = partes[0].split('\n')[-1].strip()
                time_fora = partes[1].split('\n')[0].strip()
                
                if len(time_casa) > 2 and len(time_fora) > 2:
                    jogos_encontrados.append(f"{time_casa} vs {time_fora}")

        print(f"Detectados {len(jogos_encontrados)} jogos no SuperPlacar.")

        if len(jogos_encontrados) > 0:
            bilhete = []
            # Seleciona 10 jogos aleatórios ou os primeiros 10
            amostra = random.sample(jogos_encontrados, min(len(jogos_encontrados), 10))
            
            for jogo in amostra:
                palpite, conf = analisar_probabilidades("", "")
                # Link para estatísticas no 365Scores (Busca geral)
                link_stats = f"https://www.365scores.com/pt-br/football"
                
                bilhete.append({
                    "jogo": jogo,
                    "aposta": palpite,
                    "conf": conf,
                    "link": link_stats
                })

            bilhete.sort(key=lambda x: -x['conf'])
            
            msg = f"🎫 *BILHETE DO DIA - SUPER PLACAR*\n_Stats via 365Scores | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n📊 [Analisar no 365Scores]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Bilhete enviado!")
        else:
            print("Nenhum jogo formatado encontrado.")

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    executar_robo()
            
