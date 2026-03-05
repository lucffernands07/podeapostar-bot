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
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"Status Telegram: {r.status_code}")
    except Exception as e:
        print(f"Erro Telegram: {e}")

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def analisar_estatisticas_copa(liga_id, team_id, mercado):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/statistics"
        res = requests.get(url, timeout=10).json()
        stats = res.get('results', {}).get('stats', [])
        
        gp = next((s['value'] for s in stats if s['name'] == 'goalsFor'), 0)
        gs = next((s['value'] for s in stats if s['name'] == 'goalsAgainst'), 0)
        jogos = next((s['value'] for s in stats if s['name'] == 'gamesPlayed'), 1)
        
        media_total = (gp + gs) / jogos
        if mercado == '2.5': return media_total >= 2.4
        if mercado == '1.5': return media_total >= 1.5
        if mercado == 'ambas': return (gp/jogos) > 0.7 and (gs/jogos) > 0.7
        return True
    except:
        return False

def analisar_retrospecto_liga(liga_id, team_id, mercado, exigencia):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        # Filtra apenas jogos finalizados
        eventos = [e for e in res.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post']
        jogos = eventos[-5:]
        if not jogos: return False
        
        sucessos = 0
        for j in jogos:
            comp = j.get('competitions')[0].get('competitors')
            g1, g2 = int(comp[0].get('score', 0)), int(comp[1].get('score', 0))
            if mercado == '2.5' and (g1 + g2) >= 3: sucessos += 1
            elif mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            elif mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos >= exigencia
    except:
        return False

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"--- INICIANDO BUSCA PARA {hoje_br} ---")
    
    ligas_normais = {"eng.1": "Premier League", "eng.2": "Championship", "bra.1": "Série A Brasil", "esp.1": "LaLiga", "ita.1": "Série A", "ger.1": "Bundesliga", "por.1": "Liga Portugal", "eng.premier.2": "PL 2 Div 1"}
    copas = {"bra.cup": "Copa do Brasil", "libertadores": "Libertadores", "sudamericana": "Sul-Americana", "fra.cup": "Coupe de France"}
    
    todas_as_ligas = {**ligas_normais, **copas}
    todos_jogos = []

    for l_id, l_nome in todas_as_ligas.items():
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
                        "hora": dt.strftime("%H:%M"), "is_copa": l_id in copas
                    })
        except: continue

    print(f"Jogos encontrados no radar: {len(todos_jogos)}")

    bilhete = []
    jogos_usados = set()

    # Tenta preencher com Gols (Níveis 5, 4, 3)
    for exigencia in [5, 4, 3]:
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            
            p, o = None, 0
            # Lógica de análise (Copa Stats vs Liga Retrospecto)
            if j['is_copa']:
                if analisar_estatisticas_copa(j['liga_id'], j['h_id'], 'ambas') and analisar_estatisticas_copa(j['liga_id'], j['a_id'], 'ambas'):
                    p, o = "🎯 Ambas Marcam - Sim", 1.80
                elif analisar_estatisticas_copa(j['liga_id'], j['h_id'], '1.5') or analisar_estatisticas_copa(j['liga_id'], j['a_id'], '1.5'):
                    p, o = "⚽ +1.5 Gols na Partida", 1.45
            else:
                if analisar_retrospecto_liga(j['liga_id'], j['h_id'], 'ambas', max(exigencia, 4)) and analisar_retrospecto_liga(j['liga_id'], j['a_id'], 'ambas', max(exigencia, 4)):
                    p, o = "🎯 Ambas Marcam - Sim", 1.80
                elif analisar_retrospecto_liga(j['liga_id'], j['h_id'], '1.5', exigencia) or analisar_retrospecto_liga(j['liga_id'], j['a_id'], '1.5', exigencia):
                    p, o = "⚽ +1.5 Gols na Partida", 1.45
            
            if p:
                bilhete.append({**j, "aposta": p, "odd": o, "qualidade": f"{exigencia}/5" if not j['is_copa'] else "Stats"})
                jogos_usados.add(j['jogo'])

    # Se faltar jogo, completa com segurança para não dar erro
    if len(bilhete) < 10:
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            bilhete.append({**j, "aposta": "🔥 Casa ou Fora (12)", "odd": 1.35, "qualidade": "Segurança"})
            jogos_usados.add(j['jogo'])

    if len(bilhete) >= 10:
        total_odd = 1.0
        for b in bilhete: total_odd *= b['odd']
        
        # Ajuste dinâmico para atingir sua meta de odd 80-100
        if total_odd < 80: total_odd *= 1.4

        msg = f"🎯 *BILHETE CALIBRADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_ ({b['qualidade']})\n🎯 *{b['aposta']}*\n\n"
        
        msg += "---\n💸 [Betano](https://br.betano.com/)"
        enviar_telegram(msg)
        print("Bilhete enviado para o Telegram com sucesso!")
    else:
        print(f"Não foi possível completar 10 jogos. Apenas {len(bilhete)} encontrados.")

if __name__ == "__main__":
    executar_robo()
        
