import os
import requests
import random
from datetime import datetime, timedelta

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

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def definir_palpite_estrategico():
    # Mercado e Odd Estimada
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 1.45),
        ("⚽ +2.5 Gols na Partida", 1.90),
        ("🎯 Ambas Marcam - Sim", 1.80),
        ("🛡️ Empate Anula Fav.", 1.40),
        ("🔥 Casa ou Fora (12)", 1.35),
        ("⚽ +0.5 Gols (Base Segura)", 1.10)
    ]
    return random.choice(opcoes)

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Buscando o bilhete mais próximo de Odd 100...")
    
    ligas = {
        "bra.1": "Série A Brasil", "bra.2": "Série B Brasil", "bra.copa_do_brasil": "Copa do Brasil",
        "bra.camp_paulista": "Paulistão", "bra.camp_carioca": "Cariocão",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)", "esp.1": "LaLiga (Esp)", "esp.copa_del_rey": "Copa del Rey (Esp)",
        "ita.1": "Série A (Ita)", "ita.coppa_italia": "Coppa Italia (Ita)", "ger.1": "Bundesliga (Ale)",
        "por.1": "Liga Portugal (Por)", "uefa.champions": "Champions League",
        "ned.1": "Eredivisie (Hol)", "aut.1": "Bundesliga (Aut)", "bel.1": "Pro League (Bel)", "usa.1": "MLS (EUA)"
    }

    jogos_hoje = []
    for liga_id, liga_nome in ligas.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            for evento in data.get('events', []):
                dt_br = datetime.fromisoformat(evento.get('date').replace('Z', '')) - timedelta(hours=3)
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    jogos_hoje.append({
                        "liga": liga_nome,
                        "jogo": evento.get('name').replace(' at ', ' x ').replace(' & ', ' x '),
                        "hora": dt_br.strftime("%H:%M"),
                        "link": evento.get('links')[0].get('href')
                    })
        except: continue

    if len(jogos_hoje) < 10:
        print("Jogos insuficientes.")
        return

    # --- LÓGICA DE APROXIMAÇÃO ---
    melhor_bilhete = None
    melhor_odd = 0
    alvo = 100.0

    # Faz 5000 simulações para encontrar a combinação mais próxima de 100
    for _ in range(5000):
        selecao = random.sample(jogos_hoje, 10)
        odd_atual = 1.0
        lista_atual = []

        for jogo in selecao:
            palpite, odd_est = definir_palpite_estrategico()
            odd_atual *= odd_est
            lista_atual.append({**jogo, "aposta": palpite, "odd": odd_est})

        # Regra: Tem que ser a maior possível, mas sem passar de 100
        if odd_atual <= alvo and odd_atual > melhor_odd:
            melhor_odd = odd_atual
            melhor_bilhete = lista_atual

    if melhor_bilhete:
        msg = f"🎯 *BILHETE DO DIA: ODD {melhor_odd:.2f}*\n"
        msg += f"_Foco: Máxima aproximação de 100x | HOJE ({hoje_br})_\n\n"
        
        for i, j in enumerate(melhor_bilhete, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
        
        msg += "---\n"
        msg += "💸 *APOSTAR AGORA:*\n"
        msg += "🔹 [Ir para Bet365](https://www.bet365.com/#/AS/B1/)\n"
        msg += "🔸 [Ir para Betano](https://br.betano.com/sport/futebol/)\n\n"
        msg += "⚠️ _Odds estimadas. Confira no site das casas._"
        
        enviar_telegram(msg)
        print(f"Sucesso! Bilhete enviado com Odd {melhor_odd:.2f}")
    else:
        print("Nenhuma combinação válida encontrada.")

if __name__ == "__main__":
    executar_robo()
    
