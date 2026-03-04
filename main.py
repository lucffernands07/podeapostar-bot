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

def analisar_retrospecto(liga_id, team_id, mercado):
    """
    Analisa os últimos 5 jogos para validar o mercado.
    Mercados: '1.5', '2.5', 'ambas'
    Retorna True se o critério for atendido em pelo menos 60% dos jogos.
    """
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        jogos = res.get('events', [])[-5:] # Pega os últimos 5
        
        sucessos = 0
        for jogo in jogos:
            score = jogo.get('competitions')[0].get('competitors')
            gols_casa = int(score[0].get('score', 0))
            gols_fora = int(score[1].get('score', 0))
            total = gols_casa + gols_fora
            ambas = gols_casa > 0 and gols_fora > 0
            
            if mercado == '1.5' and total >= 2: sucessos += 1
            if mercado == '2.5' and total >= 3: sucessos += 1
            if mercado == 'ambas' and ambas: sucessos += 1
            
        return sucessos >= 3 # Valida se ocorreu em pelo menos 3 de 5 jogos
    except:
        return True # Em caso de erro na API, mantém o palpite por precaução

def checar_motivacao(liga_id, home_id, away_id):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/standings"
        res = requests.get(url, timeout=10).json()
        standings = res['standings']['entries']
        total_times = len(standings)
        
        pos_home = next(i for i, s in enumerate(standings) if s['team']['id'] == home_id) + 1
        pos_away = next(i for i, s in enumerate(standings) if s['team']['id'] == away_id) + 1
        
        home_int = pos_home <= 5 or pos_home > (total_times - 5)
        away_int = pos_away <= 5 or pos_away > (total_times - 5)
        
        # Só True se um briga por algo e o outro está no meio (cumpre tabela)
        return (home_int and not away_int) or (away_int and not home_int)
    except: return False

def definir_palpite_com_prioridade(contador_25, jogo, liga_id, h_id, a_id):
    # Validamos o retrospecto para cada mercado de gols
    valid_15 = analisar_retrospecto(liga_id, h_id, '1.5') or analisar_retrospecto(liga_id, a_id, '1.5')
    valid_ambas = analisar_retrospecto(liga_id, h_id, 'ambas') and analisar_retrospecto(liga_id, a_id, 'ambas')
    
    opcoes = [
        ("🔥 Casa ou Fora (12)", 1.35, 35),
        ("🛡️ Empate Anula Fav.", 1.40, 20),
        ("⚽ +0.5 Gols (Base Segura)", 1.10, 20),
    ]

    # Só adiciona mercados de gols se o retrospecto dos últimos 5 jogos for bom
    if valid_15:
        opcoes.append(("⚽ +1.5 Gols na Partida", 1.45, 55))
    if valid_ambas:
        opcoes.append(("🎯 Ambas Marcam - Sim", 1.80, 25))
    
    # Trava absoluta de 1 jogo de +2.5 e precisa de motivação de tabela + retrospecto
    if contador_25 < 1 and jogo['motivacao_gols']:
        if analisar_retrospecto(liga_id, h_id, '2.5') or analisar_retrospecto(liga_id, a_id, '2.5'):
            opcoes.append(("⚽ +2.5 Gols na Partida", 1.95, 15))

    mercados = [o[0] for o in opcoes]
    odds = [o[1] for o in opcoes]
    pesos = [o[2] for o in opcoes]
    escolha = random.choices(list(zip(mercados, odds)), weights=pesos, k=1)[0]
    return escolha[0], escolha[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Escaneando retrospecto e tabela...")
    
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
                    
                    motivacao = checar_motivacao(liga_id, h_team['team']['id'], a_team['team']['id'])
                    
                    jogos_hoje.append({
                        "liga": liga_nome, "liga_id": liga_id,
                        "home_id": h_team['team']['id'], "away_id": a_team['team']['id'],
                        "jogo": f"{h_team['team']['displayName']} x {a_team['team']['displayName']}",
                        "hora": dt_br.strftime("%H:%M"), "link": evento['links'][0]['href'],
                        "motivacao_gols": motivacao
                    })
        except: continue

    if len(jogos_hoje) < 10: return

    melhor_bilhete, melhor_odd = None, 0
    for _ in range(3000): # Simulações
        selecao = random.sample(jogos_hoje, 10)
        odd_at, lista_at, c25 = 1.0, [], 0
        for jogo in selecao:
            p, o = definir_palpite_com_prioridade(c25, jogo, jogo['liga_id'], jogo['home_id'], jogo['away_id'])
            if "+2.5" in p: c25 += 1
            odd_at *= o
            lista_at.append({**jogo, "aposta": p, "odd": o})

        if odd_at <= 100.0 and odd_at > melhor_odd:
            melhor_odd, melhor_bilhete = odd_at, lista_at

    if melhor_bilhete:
        melhor_bilhete = sorted(melhor_bilhete, key=lambda x: x['liga'])
        ligas_no_bilhete = sorted(list(set([j['liga'] for j in melhor_bilhete])))
        resumo_ligas = "\n".join([f"🔹 {l}" for l in ligas_no_bilhete])

        msg = f"🎯 *BILHETE CALIBRADO: ODD {melhor_odd:.2f}/100*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas}\n\n"
        msg += f"⚠️ _Filtro: Retrospecto (Últimos 5 jogos) + Tabela (Máx 1 de +2.5)_\n\n"
        
        for i, j in enumerate(melhor_bilhete, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
