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

def analisar_retrospecto(liga_id, team_id, mercado, exigencia):
    """
    Analisa os últimos 5 jogos. 
    exigencia: número de sucessos necessários (5, 4 ou 3)
    """
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        jogos = res.get('events', [])[-5:]
        
        sucessos = 0
        for jogo in jogos:
            score = jogo.get('competitions')[0].get('competitors')
            g1 = int(score[0].get('score', 0))
            g2 = int(score[1].get('score', 0))
            total = g1 + g2
            ambas = g1 > 0 and g2 > 0
            
            if mercado == '1.5' and total >= 2: sucessos += 1
            if mercado == '2.5' and total >= 3: sucessos += 1
            if mercado == 'ambas' and ambas: sucessos += 1
            
        return sucessos >= exigencia
    except:
        return False

def checar_motivacao(liga_id, home_id, away_id):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/standings"
        res = requests.get(url, timeout=10).json()
        standings = res['standings']['entries']
        total = len(standings)
        pos_h = next(i for i, s in enumerate(standings) if s['team']['id'] == home_id) + 1
        pos_a = next(i for i, s in enumerate(standings) if s['team']['id'] == away_id) + 1
        return (pos_h <= 5 or pos_h > total-5) or (pos_a <= 5 or pos_a > total-5)
    except: return False

def definir_palpite(c25, jogo, liga_id, h_id, a_id, exigencia):
    v15 = analisar_retrospecto(liga_id, h_id, '1.5', exigencia) or analisar_retrospecto(liga_id, a_id, '1.5', exigencia)
    v_ambas = analisar_retrospecto(liga_id, h_id, 'ambas', exigencia) and analisar_retrospecto(liga_id, a_id, 'ambas', exigencia)
    
    opcoes = [("🔥 Casa ou Fora (12)", 1.35, 30), ("🛡️ Empate Anula Fav.", 1.40, 20), ("⚽ +0.5 Gols", 1.10, 20)]
    if v15: opcoes.append(("⚽ +1.5 Gols na Partida", 1.45, 60))
    if v_ambas: opcoes.append(("🎯 Ambas Marcam - Sim", 1.80, 25))
    if c25 < 1 and jogo['motivacao'] and (analisar_retrospecto(liga_id, h_id, '2.5', exigencia) or analisar_retrospecto(liga_id, a_id, '2.5', exigencia)):
        opcoes.append(("⚽ +2.5 Gols na Partida", 1.95, 10))

    choice = random.choices(list(zip([o[0] for o in opcoes], [o[1] for o in opcoes])), weights=[o[2] for o in opcoes], k=1)[0]
    return choice[0], choice[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    ligas = {"bra.1": "Série A Brasil", "eng.1": "Premier League", "esp.1": "LaLiga", "ita.1": "Série A (Ita)", "ger.1": "Bundesliga", "por.1": "Liga Portugal"}
    
    # Tentativa em cascata: 5/5 -> 4/5 -> 3/5
    for exigencia in [5, 4, 3]:
        print(f"Tentando gerar bilhete com exigência {exigencia}/5...")
        jogos_validos = []
        for l_id, l_nome in ligas.items():
            try:
                data = requests.get(f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard", timeout=15).json()
                for ev in data.get('events', []):
                    dt = datetime.fromisoformat(ev['date'].replace('Z', '')) - timedelta(hours=3)
                    if dt.strftime('%Y-%m-%d') == hoje_br:
                        comp = ev['competitions'][0]['competitors']
                        h = next(t for t in comp if t['homeAway'] == 'home')
                        a = next(t for t in comp if t['homeAway'] == 'away')
                        jogos_validos.append({
                            "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                            "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                            "hora": dt.strftime("%H:%M"), "link": ev['links'][0]['href'],
                            "motivacao": checar_motivacao(l_id, h['team']['id'], a['team']['id'])
                        })
            except: continue

        if len(jogos_validos) >= 10:
            melhor_bilhete, melhor_odd = None, 0
            for _ in range(2000):
                selecao = random.sample(jogos_validos, 10)
                odd_at, lista_at, c25 = 1.0, [], 0
                for j in selecao:
                    p, o = definir_palpite(c25, j, j['liga_id'], j['h_id'], j['a_id'], exigencia)
                    if "+2.5" in p: c25 += 1
                    odd_at *= o
                    lista_at.append({**j, "aposta": p, "odd": o})
                if 80.0 <= odd_at <= 100.0 and odd_at > melhor_odd:
                    melhor_odd, melhor_bilhete = odd_at, lista_at
            
            if melhor_bilhete:
                msg = f"🎯 *BILHETE CALIBRADO ({exigencia}/5): ODD {melhor_odd:.2f}*\n\n"
                msg += f"⚠️ _Máximo 1 de +2.5 | Filtro de Retrospecto Ativo_\n\n"
                for i, b in enumerate(sorted(melhor_bilhete, key=lambda x: x['liga']), 1):
                    msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}*\n📊 [Estatísticas]({b['link']})\n\n"
                msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
                enviar_telegram(msg)
                return
    print("Não foi possível gerar um bilhete com os critérios mínimos.")

if __name__ == "__main__":
    executar_robo()
            
