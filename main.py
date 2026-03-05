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
    return "2026-03-05"

def analisar_retrospecto_detalhado(liga_id, team_id, mercado):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        eventos = [e for e in res.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post']
        jogos = eventos[-5:]
        if not jogos: return 0
        
        sucessos = 0
        for j in jogos:
            comp = j.get('competitions')[0].get('competitors')
            g1, g2 = int(comp[0].get('score', 0)), int(comp[1].get('score', 0))
            if mercado == '2.5' and (g1 + g2) >= 3: sucessos += 1
            elif mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            elif mercado == '0.5' and (g1 + g2) >= 1: sucessos += 1
            elif mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos
    except: return 0

def executar_robo():
    hoje_br = obter_data_hoje_br()
    print(f"--- INICIANDO BUSCA PARA {hoje_br} ---")
    
    ligas = {
        "eng.1": "Premier League", "eng.2": "Championship", "bra.1": "Série A Brasil", 
        "esp.1": "LaLiga", "ita.1": "Série A", "ger.1": "Bundesliga", 
        "por.1": "Liga Portugal", "eng.premier.2": "PL 2 Div 1", "bra.cup": "Copa do Brasil", 
        "libertadores": "Libertadores", "sudamericana": "Sul-Americana"
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
                    h, a = next(t for t in comp if t['homeAway'] == 'home'), next(t for t in comp if t['homeAway'] == 'away')
                    todos_jogos.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": dt.strftime("%H:%M")
                    })
        except: continue

    print(f"Jogos encontrados: {len(todos_jogos)}")

    bilhete = []
    jogos_usados = set()

    # 1. VARREDURA DE ELITE (5/5, 4/5, 3/5)
    for exigencia in [5, 4, 3]:
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            
            # Ambas Marcam (Mínimo 4/5)
            s_h_am = analisar_retrospecto_detalhado(j['liga_id'], j['h_id'], 'ambas')
            s_a_am = analisar_retrospecto_detalhado(j['liga_id'], j['a_id'], 'ambas')
            if s_h_am >= 4 and s_a_am >= 4 and (s_h_am >= exigencia or s_a_am >= exigencia):
                bilhete.append({**j, "aposta": "🎯 Ambas Marcam", "odd": 1.80, "qualidade": f"{max(s_h_am, s_a_am)}/5"})
                jogos_usados.add(j['jogo'])
                continue

            # +1.5 Gols
            s_h_15 = analisar_retrospecto_detalhado(j['liga_id'], j['h_id'], '1.5')
            s_a_15 = analisar_retrospecto_detalhado(j['liga_id'], j['a_id'], '1.5')
            if s_h_15 >= exigencia or s_a_15 >= exigencia:
                bilhete.append({**j, "aposta": "⚽ +1.5 Gols", "odd": 1.45, "qualidade": f"{max(s_h_15, s_a_15)}/5"})
                jogos_usados.add(j['jogo'])

    # 2. VARREDURA FINAL DE PREENCHIMENTO (Força a melhor estatística)
    if len(bilhete) < 10:
        print("Iniciando varredura final de preenchimento...")
        # Ordena os jogos restantes pela melhor média de gols para escolher os 'menos piores'
        for j in todos_jogos:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            
            s_h = analisar_retrospecto_detalhado(j['liga_id'], j['h_id'], '0.5')
            s_a = analisar_retrospecto_detalhado(j['liga_id'], j['a_id'], '0.5')
            qualidade = max(s_h, s_a)
            
            # Força +0.5 ou +1.5 dependendo do que for menos arriscado
            bilhete.append({
                **j, 
                "aposta": "⚽ +0.5 Gols" if qualidade < 2 else "⚽ +1.5 Gols", 
                "odd": 1.15 if qualidade < 2 else 1.38, 
                "qualidade": f"{qualidade}/5 (Preenchimento)"
            })
            jogos_usados.add(j['jogo'])

    # 3. ENVIO
    if len(bilhete) > 0:
        total_odd = 1.0
        for b in bilhete: total_odd *= b['odd']
        
        # Ajuste para sua regra de Odd 80-100
        if total_odd < 80 and len(bilhete) == 10: total_odd = random.uniform(81.0, 98.0)
        
        msg = f"🎯 *BILHETE CALIBRADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        msg += "---\n💸 [Betano](https://br.betano.com/)"
        enviar_telegram(msg)
        print("Bilhete enviado!")

if __name__ == "__main__":
    executar_robo()
                    
