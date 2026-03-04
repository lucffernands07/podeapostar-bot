import os
import requests
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def checar_motivacao(liga_id, home_id, away_id):
    """
    Verifica se o jogo tem potencial para +2.5 baseado na tabela.
    Retorna True se houver disputa (Top 5 ou Z5) contra time de meio de tabela.
    """
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/standings"
        res = requests.get(url, timeout=10).json()
        standings = res['standings']['entries']
        total_times = len(standings)
        
        pos_home = next(i for i, s in enumerate(standings) if s['team']['id'] == home_id) + 1
        pos_away = next(i for i, s in enumerate(standings) if s['team']['id'] == away_id) + 1
        
        # Critério: Algum time no Top 5 ou nos últimos 5 (Z5)
        home_interessado = pos_home <= 5 or pos_home > (total_times - 5)
        away_interessado = pos_away <= 5 or pos_away > (total_times - 5)
        
        # Se um quer muito e o outro está no meio (cumprindo tabela), o jogo tende a gols
        if (home_interessado and not away_interessado) or (away_interessado and not home_interessado):
            return True
        return False
    except:
        return False # Na dúvida ou erro (copas), não arrisca o +2.5

def definir_palpite_com_prioridade(contador_25, tem_motivacao_gols):
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 1.45, 50),
        ("🔥 Casa ou Fora (12)", 1.35, 30),
        ("🎯 Ambas Marcam - Sim", 1.80, 25),
        ("🛡️ Empate Anula Fav.", 1.40, 20),
        ("⚽ +0.5 Gols (Base Segura)", 1.10, 20),
    ]
    
    # SÓ libera +2.5 se tiver a motivação de tabela que você pediu E limite de 1 por bilhete
    if contador_25 < 1 and tem_motivacao_gols:
        opcoes.append(("⚽ +2.5 Gols na Partida", 1.95, 15))

    mercados = [o[0] for o in opcoes]
    odds = [o[1] for o in opcoes]
    pesos = [o[2] for o in opcoes]
    escolha = random.choices(list(zip(mercados, odds)), weights=pesos, k=1)[0]
    return escolha[0], escolha[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Analisando Tabela e Motivação...")
    
    ligas_config = {
        "bra.1": "Série A Brasil", "eng.1": "Premier League (Ing)", 
        "esp.1": "LaLiga (Esp)", "ita.1": "Série A (Ita)", 
        "ger.1": "Bundesliga (Ale)", "por.1": "Liga Portugal (Por)"
    }

    jogos_hoje = []
    for liga_id, liga_nome in ligas_config.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            data = requests.get(url, timeout=15).json()
            for evento in data.get('events', []):
                dt_br = datetime.fromisoformat(evento.get('date').replace('Z', '')) - timedelta(hours=3)
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    comp = evento['competitions'][0]['competitors']
                    h_team = next(t for t in comp if t['homeAway'] == 'home')
                    a_team = next(t for t in comp if t['homeAway'] == 'away')
                    
                    # Nova checagem de motivação
                    motivacao = checar_motivacao(liga_id, h_team['team']['id'], a_team['team']['id'])
                    
                    jogos_hoje.append({
                        "liga": liga_nome, "jogo": f"{h_team['team']['displayName']} x {a_team['team']['displayName']}",
                        "hora": dt_br.strftime("%H:%M"), "link": evento['links'][0]['href'],
                        "motivacao_gols": motivacao
                    })
        except: continue

    if len(jogos_hoje) < 10: return

    melhor_bilhete, melhor_odd = None, 0
    for _ in range(5000):
        selecao = random.sample(jogos_hoje, 10)
        odd_at, lista_at, c25 = 1.0, [], 0
        for jogo in selecao:
            palpite, odd_est = definir_palpite_com_prioridade(c25, jogo['motivacao_gols'])
            if "+2.5" in palpite: c25 += 1
            odd_at *= odd_est
            lista_at.append({**jogo, "aposta": palpite, "odd": odd_est})

        if odd_at <= 100.0 and odd_at > melhor_odd:
            melhor_odd, melhor_bilhete = odd_at, lista_at

    if melhor_bilhete:
        melhor_bilhete = sorted(melhor_bilhete, key=lambda x: x['liga'])
        ligas_no_bilhete = sorted(list(set([j['liga'] for j in melhor_bilhete])))
        resumo_ligas = "\n".join([f"🔹 {l}" for l in ligas_no_bilhete])

        msg = f"🎯 *BILHETE CALIBRADO: ODD {melhor_odd:.2f}/100*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas}\n\n"
        msg += f"⚠️ _Filtro: Motivação de Tabela Ativado (Máx 1 de +2.5)_\n\n"
        
        for i, j in enumerate(melhor_bilhete, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
    
