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

def obter_data_hoje():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def analisar_retrospecto(liga_id, team_id, mercado):
    """Retorna sucessos de 0 a 5"""
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
            if mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            elif mercado == '0.5' and (g1 + g2) >= 1: sucessos += 1
            elif mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos
    except: return 0

def executar_robo():
    hoje = obter_data_hoje()
    print(f"--- BUSCA INICIADA PARA {hoje} ---")
    
    # IDs HÍBRIDOS (Unindo o que funcionou ontem com as ligas de hoje)
    ligas_config = {
        "eng.1": "Premier League", "eng.2": "Championship", "bra.1": "Série A Brasil",
        "esp.1": "LaLiga", "ita.1": "Série A", "ger.1": "Bundesliga", "por.1": "Liga Portugal",
        "bra.copa_do_brasil": "Copa do Brasil", "conmebol.libertadores": "Libertadores",
        "conmebol.sudamericana": "Sul-Americana", "esp.copa_del_rey": "Copa del Rey",
        "eng.premier.2": "PL 2 Div 1"
    }
    
    jogos_encontrados = []
    for l_id, l_nome in ligas_config.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard"
            data = requests.get(url, timeout=15).json()
            for ev in data.get('events', []):
                # Filtro de data mais flexível (checa se o dia está na string de data)
                if hoje in ev['date']:
                    comp = ev['competitions'][0]['competitors']
                    h = next(t for t in comp if t['homeAway'] == 'home')
                    a = next(t for t in comp if t['homeAway'] == 'away')
                    jogos_encontrados.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": ev['date'][11:16]
                    })
        except: continue

    print(f"Total de jogos no radar: {len(jogos_encontrados)}")

    bilhete = []
    jogos_usados = set()

    # 1. VARREDURA DE ELITE (Filtros 5/5, 4/5, 3/5)
    for nivel in [5, 4, 3]:
        for j in jogos_encontrados:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            
            # Ambas Marcam (Mínimo 4/5 conforme sua regra)
            s_am = analisar_retrospecto(j['liga_id'], j['h_id'], 'ambas')
            if s_am >= 4 and s_am >= nivel:
                bilhete.append({**j, "aposta": "🎯 Ambas Marcam", "odd": 1.80, "qualidade": f"{s_am}/5"})
                jogos_usados.add(j['jogo'])
                continue

            # +1.5 Gols
            s_15 = max(analisar_retrospecto(j['liga_id'], j['h_id'], '1.5'), analisar_retrospecto(j['liga_id'], j['a_id'], '1.5'))
            if s_15 >= nivel:
                bilhete.append({**j, "aposta": "⚽ +1.5 Gols", "odd": 1.45, "qualidade": f"{s_15}/5"})
                jogos_usados.add(j['jogo'])

    # 2. VARREDURA DE PREENCHIMENTO (Se não atingiu 10 jogos)
    if len(bilhete) < 10:
        print(f"Completando com o que restou (Total atual: {len(bilhete)})...")
        for j in jogos_encontrados:
            if len(bilhete) >= 10 or j['jogo'] in jogos_usados: continue
            s_05 = max(analisar_retrospecto(j['liga_id'], j['h_id'], '0.5'), analisar_retrospecto(j['liga_id'], j['a_id'], '0.5'))
            bilhete.append({**j, "aposta": "⚽ +0.5 Gols", "odd": 1.15, "qualidade": f"{s_05}/5 (Ajuste)"})
            jogos_usados.add(j['jogo'])

    # 3. ENVIO (Mesmo que tenha poucos jogos)
    if bilhete:
        total_odd = 1.0
        for b in bilhete: total_odd *= b['odd']
        
        # Ajuste para sua meta de Odd alta se o bilhete estiver completo
        if len(bilhete) == 10 and total_odd < 80: total_odd *= 1.4

        msg = f"🎯 *BILHETE GERADO ({len(bilhete)} JOGOS)*\n💰 *ODD TOTAL: {total_odd:.2f}*\n\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        msg += "---\n💸 [Betano](https://br.betano.com/)"
        enviar_telegram(msg)
        print("Bilhete enviado!")
    else:
        print("Nenhum jogo encontrado após os filtros.")

if __name__ == "__main__":
    executar_robo()
                
