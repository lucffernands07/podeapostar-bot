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
    Prioriza mercados de segurança. 
    Limite rigoroso de apenas 1 jogo de +2.5 gols.
    """
    # (Mercado, Odd Estimada, Peso de sorteio)
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 1.45, 50), # Prioridade alta
        ("🔥 Casa ou Fora (12)", 1.35, 30),     # Prioridade alta
        ("🎯 Ambas Marcam - Sim", 1.80, 25),    # Prioridade média
        ("🛡️ Empate Anula Fav.", 1.40, 20),
        ("⚽ +0.5 Gols (Base Segura)", 1.10, 20),
    ]
    
    # Trava: apenas 1 jogo de +2.5 por bilhete
    if contador_25 < 1:
        opcoes.append(("⚽ +2.5 Gols na Partida", 1.95, 5)) # Peso muito baixo

    mercados = [o[0] for o in opcoes]
    odds = [o[1] for o in opcoes]
    pesos = [o[2] for o in opcoes]

    escolha = random.choices(list(zip(mercados, odds)), weights=pesos, k=1)[0]
    return escolha[0], escolha[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Gerando bilhete (Foco: Segurança Máxima + Máx 1 de 2.5)...")
    
    ligas_config = {
        "bra.1": "Série A Brasil", "bra.2": "Série B Brasil", "bra.copa_do_brasil": "Copa do Brasil",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)", "esp.1": "LaLiga (Esp)", "esp.copa_del_rey": "Copa del Rey (Esp)",
        "ita.1": "Série A (Ita)", "ger.1": "Bundesliga (Ale)", "por.1": "Liga Portugal (Por)",
        "uefa.champions": "Champions League", "usa.1": "MLS (EUA)"
    }

    jogos_hoje = []
    for liga_id, liga_nome in ligas_config.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            for evento in data.get('events', []):
                dt_br = datetime.fromisoformat(evento.get('date').replace('Z', '')) - timedelta(hours=3)
                
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    competitors = evento.get('competitions')[0].get('competitors')
                    home_team = next(t.get('team').get('displayName') for t in competitors if t.get('homeAway') == 'home')
                    away_team = next(t.get('team').get('displayName') for t in competitors if t.get('homeAway') == 'away')
                    
                    jogos_hoje.append({
                        "liga": liga_nome,
                        "jogo": f"{home_team} x {away_team}",
                        "hora": dt_br.strftime("%H:%M"),
                        "link": evento.get('links')[0].get('href')
                    })
        except: continue

    if len(jogos_hoje) < 10:
        print("Jogos insuficientes.")
        return

    melhor_bilhete, melhor_odd = None, 0
    alvo = 100.0

    for _ in range(5000):
        selecao = random.sample(jogos_hoje, 10)
        odd_atual, lista_atual, c25 = 1.0, [], 0
        
        for jogo in selecao:
            palpite, odd_est = definir_palpite_com_prioridade(c25)
            if "+2.5" in palpite: c25 += 1
            odd_atual *= odd_est
            lista_atual.append({**jogo, "aposta": palpite, "odd": odd_est})

        if odd_atual <= alvo and odd_atual > melhor_odd:
            melhor_odd, melhor_bilhete = odd_atual, lista_atual

    if melhor_bilhete:
        melhor_bilhete = sorted(melhor_bilhete, key=lambda x: x['liga'])
        ligas_no_bilhete = sorted(list(set([j['liga'] for j in melhor_bilhete])))
        resumo_ligas_vertical = "\n".join([f"🔹 {liga}" for liga in ligas_no_bilhete])

        msg = f"🎯 *BILHETE CALIBRADO: ODD {melhor_odd:.2f}/100*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas_vertical}\n\n"
        msg += f"⚠️ _Máximo 1 palpite de +2.5 Gols | HOJE ({hoje_br})_\n\n"
        
        for i, j in enumerate(melhor_bilhete, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        
        enviar_telegram(msg)
        print(f"Sucesso! Bilhete com Odd {melhor_odd:.2f} enviado.")

if __name__ == "__main__":
    executar_robo()
    
