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

def definir_palpite_com_prioridade(contador_25):
    """
    Sorteia palpites priorizando mercados seguros.
    Só permite +2.5 se ainda não atingiu o limite de 3.
    """
    # Lista de opções: (Nome, Odd, Peso de Probabilidade)
    # Quanto maior o peso, mais chances de ser escolhido.
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 1.45, 40),
        ("🛡️ Empate Anula Fav.", 1.40, 25),
        ("🔥 Casa ou Fora (12)", 1.35, 25),
        ("⚽ +0.5 Gols (Base Segura)", 1.10, 30),
        ("🎯 Ambas Marcam - Sim", 1.80, 15),
    ]
    
    # Adiciona +2.5 gols apenas se ainda houver "vaga" no bilhete
    if contador_25 < 3:
        opcoes.append(("⚽ +2.5 Gols na Partida", 1.90, 10)) # Peso baixo para ser raro

    mercados = [o[0] for o in opcoes]
    odds = [o[1] for o in opcoes]
    pesos = [o[2] for o in opcoes]

    escolha = random.choices(list(zip(mercados, odds)), weights=pesos, k=1)[0]
    return escolha[0], escolha[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Buscando bilhete (Máx 3 de '+2.5') próximo a Odd 100...")
    
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

    melhor_bilhete = None
    melhor_odd = 0
    alvo = 100.0

    # 5000 simulações para achar a combinação ótima
    for _ in range(5000):
        selecao = random.sample(jogos_hoje, 10)
        odd_atual = 1.0
        lista_atual = []
        contador_25 = 0

        for jogo in selecao:
            palpite, odd_est = definir_palpite_com_prioridade(contador_25)
            if "+2.5" in palpite:
                contador_25 += 1
            
            odd_atual *= odd_est
            lista_atual.append({**jogo, "aposta": palpite, "odd": odd_est})

        # Critério: O mais perto de 100 sem estourar
        if odd_atual <= alvo and odd_atual > melhor_odd:
            melhor_odd = odd_atual
            melhor_bilhete = lista_atual

    if melhor_bilhete:
        msg = f"🎯 *BILHETE CALIBRADO: ODD {melhor_odd:.2f}*\n"
        msg += f"_Máximo 3 palpites de +2.5 Gols | HOJE ({hoje_br})_\n\n"
        
        for i, j in enumerate(melhor_bilhete, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        
        enviar_telegram(msg)
        print(f"Bilhete enviado! Odd: {melhor_odd:.2f}")

if __name__ == "__main__":
    executar_robo()
    
