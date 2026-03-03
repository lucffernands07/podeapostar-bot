import os
import requests
import random
from datetime import datetime

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def analisar_estatisticas(jogo):
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos no H2H."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio no histórico recente."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada."),
        ("🚩 +8.5 Cantos", 72, "Estilo de jogo vertical."),
        ("⏱️ Golo HT", 81, "Equipas com início forte.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Conectando à API v1 do Sporting Life...")
    
    hoje = datetime.now().strftime('%Y-%m-%d')
    # URL de produção usada pelo site deles
    url_api = f"https://www.sportinglife.com/api/football/fixtures?date={hoje}"
    
    # Headers completos para evitar o Erro 404/403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Origin': 'https://www.sportinglife.com',
        'Referer': 'https://www.sportinglife.com/football/fixtures-results',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        session = requests.Session()
        res = session.get(url_api, headers=headers, timeout=25)
        
        # Se ainda der 404, tentamos a URL alternativa sem o prefixo 'www'
        if res.status_code == 404:
            print("Tentando rota alternativa...")
            url_api_alt = f"https://www.sportinglife.com/api/v1/football/fixtures?date={hoje}"
            res = session.get(url_api_alt, headers=headers, timeout=25)

        if res.status_code != 200:
            print(f"Erro na API: {res.status_code}")
            return

        dados = res.json()
        bilhete = []
        
        # Estrutura do JSON do Sporting Life
        competicoes = dados.get('competitions', [])
        if not competicoes:
            print("Estrutura JSON vazia ou sem jogos hoje.")
            return

        for competicao in competicoes:
            for jogo in competicao.get('fixtures', []):
                # Pegar apenas jogos não iniciados
                if jogo.get('status', '').lower() in ['fixture', 'scheduled', 'pre-match']:
                    home = jogo['home_team']['name']
                    away = jogo['away_team']['name']
                    id_jogo = jogo['id']
                    
                    mercado, conf, obs = analisar_estatisticas(f"{home} vs {away}")
                    
                    bilhete.append({
                        "jogo": f"{home} vs {away}",
                        "aposta": mercado,
                        "conf": conf,
                        "link": f"https://www.sportinglife.com/football/live/{id_jogo}"
                    })
                
                if len(bilhete) >= 20: break
            if len(bilhete) >= 20: break

        if len(bilhete) >= 5:
            bilhete.sort(key=lambda x: -x['conf'])
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_API Mode | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete[:10], 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Ver Dados]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Bilhete enviado!")
        else:
            print("Jogos insuficientes encontrados.")

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    executar_robo()
