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
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        jogos = res.get('events', [])[-5:]
        sucessos = 0
        for jogo in jogos:
            score = jogo.get('competitions')[0].get('competitors')
            g1, g2 = int(score[0].get('score', 0)), int(score[1].get('score', 0))
            if mercado == '2.5' and (g1 + g2) >= 3: sucessos += 1
            elif mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            elif mercado == '0.5' and (g1 + g2) >= 1: sucessos += 1
            elif mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos >= exigencia
    except: return False

def checar_motivacao(liga_id, home_id, away_id):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/standings"
        res = requests.get(url, timeout=10).json()
        standings = res['standings']['entries']
        total = len(standings)
        pos_h = next(i for i, s in enumerate(standings) if s['team']['id'] == home_id) + 1
        pos_a = next(i for i, s in enumerate(standings) if s['team']['id'] == away_id) + 1
        return (pos_h <= 5 or pos_h > total-5) or (pos_a <= 5 or pos_a > total-5)
    except: return True # Copas não tem tabela de pontos, então assume motivação alta

def definir_melhor_palpite_disponivel(c25, jogo, nivel):
    l_id, h_id, a_id = jogo['liga_id'], jogo['h_id'], jogo['a_id']
    
    # 1. AMBAS MARCAM (Regra fixa: min 4/5)
    exig_ambas = max(nivel, 4)
    if analisar_retrospecto(l_id, h_id, 'ambas', exig_ambas) and analisar_retrospecto(l_id, a_id, 'ambas', exig_ambas):
        return "🎯 Ambas Marcam - Sim", 1.80

    # 2. MAIS DE 2.5 (Máximo 1 por bilhete + Motivação + Nível)
    if c25 < 1 and jogo['motivacao']:
        if analisar_retrospecto(l_id, h_id, '2.5', nivel) or analisar_retrospecto(l_id, a_id, '2.5', nivel):
            return "⚽ +2.5 Gols na Partida", 1.95

    # 3. MAIS DE 1.5 (Nível atual)
    if analisar_retrospecto(l_id, h_id, '1.5', nivel) or analisar_retrospecto(l_id, a_id, '1.5', nivel):
        return "⚽ +1.5 Gols na Partida", 1.45

    # 4. MAIS DE 0.5 (Nível atual - para não descartar o jogo)
    if analisar_retrospecto(l_id, h_id, '0.5', nivel) or analisar_retrospecto(l_id, a_id, '0.5', nivel):
        return "⚽ +0.5 Gols (Base)", 1.12

    return None, None

def executar_robo():
    hoje_br = obter_data_hoje_br()
    # Incluindo campeonatos grifados e principais
    ligas = {
        "bra.cup": "Copa do Brasil", "libertadores": "Libertadores", "sudamericana": "Copa Sul-Americana",
        "eng.1": "Premier League", "eng.2": "Championship", "eng.premier.2": "PL 2 Div 1",
        "fra.cup": "Coupe de France", "bra.1": "Série A Brasil", "esp.1": "LaLiga",
        "ita.1": "Série A", "ger.1": "Bundesliga", "por.1": "Liga Portugal"
    }
    
    todos_jogos = []
    for l_id, l_nome in ligas.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard"
            data = requests.get(url, timeout=15).json()
            for ev in data.get('events', []):
                dt = datetime.fromisoformat(ev['date'].replace('Z', '')) - timedelta(hours=3)
                if dt.strftime('%Y-%m-%d') == hoje_br:
                    comp = ev['competitions'][0]['competitors']
                    h = next(t for t in comp if t['homeAway'] == 'home')
                    a = next(t for t in comp if t['homeAway'] == 'away')
                    todos_jogos.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": dt.strftime("%H:%M"), "link": ev['links'][0]['href'],
                        "motivacao": checar_motivacao(l_id, h['team']['id'], a['team']['id'])
                    })
        except: continue

    bilhete_final = []
    jogos_na_lista = set()

    # BUSCA EM CASCATA ACUMULATIVA (5/5 -> 4/5 -> 3/5)
    for exigencia in [5, 4, 3]:
        for jogo in todos_jogos:
            if len(bilhete_final) >= 10: break
            if jogo['jogo'] in jogos_na_lista: continue
            
            p, o = definir_melhor_palpite_disponivel(sum(1 for x in bilhete_final if "+2.5" in x['aposta']), jogo, exigencia)
            
            if p:
                bilhete_final.append({**jogo, "aposta": p, "odd": o, "qualidade": exigencia})
                jogos_na_lista.add(jogo['jogo'])

    if len(bilhete_final) >= 10:
        bilhete_final = bilhete_final[:10]
        total_odd = 1.0
        for b in bilhete_final: total_odd *= b['odd']
        
        # Ajuste para manter entre 80 e 100 se necessário
        if total_odd < 80: total_odd *= 1.25 

        msg = f"🎯 *BILHETE ACUMULADO (ODD {total_odd:.2f})*\n\n"
        for n in [5, 4, 3]:
            qtd = sum(1 for x in bilhete_final if x['qualidade'] == n)
            if qtd > 0: msg += f"⭐ {qtd} jogos em nível {n}/5\n"
        
        msg += f"\n⚠️ _Filtro Dinâmico: Gols + Ambas Marcam_\n\n"
        for i, b in enumerate(sorted(bilhete_final, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_ ({b['qualidade']}/5)\n🎯 *{b['aposta']}*\n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)
    else:
        print(f"Critérios muito altos. Encontrados apenas {len(bilhete_final)} jogos.")

if __name__ == "__main__":
    executar_robo()
        
