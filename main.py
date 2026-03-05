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

def analisar_estatisticas_copa(liga_id, team_id, mercado):
    """
    Para COPAS: Analisa as estatísticas gerais da temporada (média de gols).
    """
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/statistics"
        res = requests.get(url, timeout=10).json()
        stats = res.get('results', {}).get('stats', [])
        
        # Pega média de gols marcados e sofridos
        gp = next((s['value'] for s in stats if s['name'] == 'goalsFor'), 0)
        gs = next((s['value'] for s in stats if s['name'] == 'goalsAgainst'), 0)
        jogos = next((s['value'] for s in stats if s['name'] == 'gamesPlayed'), 1)
        
        media_total = (gp + gs) / jogos
        tem_gol = gp > 0 and gs > 0 # Base para "Ambas Marcam"

        if mercado == '2.5': return media_total >= 2.5
        if mercado == '1.5': return media_total >= 1.6
        if mercado == 'ambas': return gp/jogos > 0.8 and gs/jogos > 0.8
        return True
    except: return True

def analisar_retrospecto_liga(liga_id, team_id, mercado, exigencia):
    """
    Para LIGAS: Mantém sua regra de 5/5, 4/5 ou 3/5.
    """
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        jogos = [e for e in res.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
        if not jogos: return False
        sucessos = 0
        for j in jogos:
            comp = j.get('competitions')[0].get('competitors')
            g1, g2 = int(comp[0].get('score', 0)), int(comp[1].get('score', 0))
            if mercado == '2.5' and (g1 + g2) >= 3: sucessos += 1
            elif mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            elif mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos >= exigencia
    except: return False

def executar_robo():
    hoje_br = obter_data_hoje_br()
    # Diferenciamos LIGAS de COPAS
    ligas_normais = {"eng.1": "Premier League", "eng.2": "Championship", "bra.1": "Série A Brasil", "esp.1": "LaLiga", "ita.1": "Série A", "ger.1": "Bundesliga", "por.1": "Liga Portugal", "eng.premier.2": "PL 2 Div 1"}
    copas = {"bra.cup": "Copa do Brasil", "libertadores": "Libertadores", "sudamericana": "Sul-Americana", "fra.cup": "Coupe de France"}
    
    todas_as_ligas = {**ligas_normais, **copas}
    todos_jogos = []

    for l_id, l_nome in todas_as_ligas.items():
        try:
            data = requests.get(f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard", timeout=15).json()
            for ev in data.get('events', []):
                dt = datetime.fromisoformat(ev['date'].replace('Z', '')) - timedelta(hours=3)
                if dt.strftime('%Y-%m-%d') == hoje_br:
                    comp = ev['competitions'][0]['competitors']
                    h, a = next(t for t in comp if t['homeAway'] == 'home'), next(t for t in comp if t['homeAway'] == 'away')
                    todos_jogos.append({"liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'], "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}", "hora": dt.strftime("%H:%M"), "is_copa": l_id in copas})
        except: continue

    bilhete = []
    jogos_usados = set()

    for exigencia in [5, 4, 3]:
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            
            # Escolha da função baseada no tipo de campeonato
            if j['is_copa']:
                val_ambas = analisar_estatisticas_copa(j['liga_id'], j['h_id'], 'ambas') and analisar_estatisticas_copa(j['liga_id'], j['a_id'], 'ambas')
                val_15 = analisar_estatisticas_copa(j['liga_id'], j['h_id'], '1.5') or analisar_estatisticas_copa(j['liga_id'], j['a_id'], '1.5')
                val_25 = analisar_estatisticas_copa(j['liga_id'], j['h_id'], '2.5') or analisar_estatisticas_copa(j['liga_id'], j['a_id'], '2.5')
            else:
                val_ambas = analisar_retrospecto_liga(j['liga_id'], j['h_id'], 'ambas', max(exigencia, 4)) and analisar_retrospecto_liga(j['liga_id'], j['a_id'], 'ambas', max(exigencia, 4))
                val_15 = analisar_retrospecto_liga(j['liga_id'], j['h_id'], '1.5', exigencia) or analisar_retrospecto_liga(j['liga_id'], j['a_id'], '1.5', exigencia)
                val_25 = analisar_retrospecto_liga(j['liga_id'], j['h_id'], '2.5', exigencia) or analisar_retrospecto_liga(j['liga_id'], j['a_id'], '2.5', exigencia)

            # Define Palpite
            p, o = None, 0
            if val_ambas: p, o = "🎯 Ambas Marcam - Sim", 1.80
            elif sum(1 for x in bilhete if "+2.5" in x['aposta']) < 1 and val_25: p, o = "⚽ +2.5 Gols na Partida", 1.95
            elif val_15: p, o = "⚽ +1.5 Gols na Partida", 1.45
            
            if p:
                bilhete.append({**j, "aposta": p, "odd": o, "qualidade": exigencia if not j['is_copa'] else "Stats"})
                jogos_usados.add(j['jogo'])

    # Fallback para completar 10 jogos
    if len(bilhete) < 10:
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            bilhete.append({**j, "aposta": "🔥 Casa ou Fora (12)", "odd": 1.35, "qualidade": "Segurança"})
            jogos_usados.add(j['jogo'])

    if len(bilhete) >= 10:
        total_odd = 1.0
        for b in bilhete: total_odd *= b['odd']
        msg = f"🎯 *BILHETE CALIBRADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_ ({b['qualidade']})\n🎯 *{b['aposta']}*\n\n"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
                    
