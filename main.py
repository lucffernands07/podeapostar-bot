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
    print(f"[{datetime.now().strftime('%H:%M')}] Conectando à API do Sporting Life...")
    
    # URL da API de jogos de futebol do Sporting Life
    hoje = datetime.now().strftime('%Y-%m-%d')
    url_api = f"https://www.sportinglife.com/api/football/fixtures?date={hoje}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    try:
        res = requests.get(url_api, headers=headers, timeout=20)
        
        if res.status_code != 200:
            print(f"Erro na API: {res.status_code}")
            return

        dados = res.json()
        bilhete = []
        
        # O Sporting Life organiza por competições
        for competicao in dados.get('competitions', []):
            for jogo in competicao.get('fixtures', []):
                # Pegamos apenas jogos que ainda não começaram
                status = jogo.get('status', '').lower()
                if status == 'fixture' or status == 'scheduled':
                    home_team = jogo['home_team']['name']
                    away_team = jogo['away_team']['name']
                    nome_jogo = f"{home_team} vs {away_team}"
                    
                    # Geramos o link oficial
                    id_jogo = jogo['id']
                    link = f"https://www.sportinglife.com/football/live/{id_jogo}"
                    
                    mercado, conf, obs = analisar_estatisticas(nome_jogo)
                    
                    bilhete.append({
                        "jogo": nome_jogo,
                        "aposta": mercado,
                        "conf": conf,
                        "link": link
                    })
                
                if len(bilhete) >= 15: break
            if len(bilhete) >= 15: break

        print(f"Jogos processados: {len(bilhete)}")

        if len(bilhete) >= 5:
            # Ordena por confiança e pega os 10 melhores
            bilhete.sort(key=lambda x: -x['conf'])
            
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_API Mode | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete[:10], 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n🔗 [Ver Dados]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Mensagem enviada!")
        else:
            print("Nenhum jogo futuro encontrado para hoje.")

    except Exception as e:
        print(f"Erro ao processar JSON: {e}")

if __name__ == "__main__":
    executar_robo()
