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

def obter_stats_basicas(liga_id, team_id):
    """Retorna média de gols pro e contra quando não há histórico 5/5"""
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/statistics"
        res = requests.get(url, timeout=10).json()
        stats = res.get('results', {}).get('stats', [])
        gp = next((s['value'] for s in stats if s['name'] == 'goalsFor'), 0)
        gs = next((s['value'] for s in stats if s['name'] == 'goalsAgainst'), 0)
        jogos = next((s['value'] for s in stats if s['name'] == 'gamesPlayed'), 1)
        return (gp + gs) / jogos
    except: return 0

def analisar_partida(j, contador_25):
    """
    Funil de Decisão:
    1. Tenta Ambas Marcam (4/5 ou 5/5)
    2. Tenta +2.5 (5/5 e se houver vaga)
    3. Tenta +1.5 (5/5 -> 4/5 -> 3/5)
    4. Tenta +0.5 (Baseado em Médias Pro/Contra - 0/5)
    """
    l_id, h_id, a_id = j['liga_id'], j['h_id'], j['a_id']
    
    def get_sucessos(mercado):
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/teams/{h_id}/schedule"
            res = requests.get(url, timeout=10).json()
            evs = [e for e in res.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
            if not evs: return 0
            s = 0
            for ev in evs:
                c = ev['competitions'][0]['competitors']
                g1, g2 = int(c[0].get('score', 0)), int(c[1].get('score', 0))
                if mercado == '2.5' and (g1+g2) >= 3: s += 1
                elif mercado == '1.5' and (g1+g2) >= 2: s += 1
                elif mercado == 'ambas' and (g1 > 0 and g2 > 0): s += 1
            return s
        except: return 0

    # Teste Ambas Marcam (Mínimo 4/5 conforme regra)
    s_am = get_sucessos('ambas')
    if s_am >= 4:
        return "🎯 Ambas Marcam", 1.85, f"{s_am}/5"

    # Teste +2.5 (Apenas 1 no bilhete)
    if contador_25 < 1:
        s_25 = get_sucessos('2.5')
        if s_25 >= 4:
            return "🔥 +2.5 Gols", 2.10, f"{s_25}/5"

    # Teste +1.5 (Funil 5/5 até 3/5)
    s_15 = get_sucessos('1.5')
    if s_15 >= 3:
        return "⚽ +1.5 Gols", 1.48, f"{s_15}/5"

    # Fallback: +0.5 Gols (Análise de Médias Pro/Contra - 0/5)
    media = obter_stats_basicas(l_id, h_id)
    return "🛡️ +0.5 Gols", 1.22, "0/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    ligas_config = {
        "eng.1": "Premier League", "bra.1": "Série A Brasil", "conmebol.libertadores": "Libertadores",
        "conmebol.sudamericana": "Sul-Americana", "esp.1": "LaLiga", "ita.1": "Série A", 
        "ger.1": "Bundesliga", "por.1": "Liga Portugal", "bra.copa_do_brasil": "Copa do Brasil"
    }
    
    radar = []
    for l_id, l_nome in ligas_config.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard"
            data = requests.get(url, timeout=15).json()
            for ev in data.get('events', []):
                if hoje in ev['date']:
                    comp = ev['competitions'][0]['competitors']
                    h, a = next(t for t in comp if t['homeAway'] == 'home'), next(t for t in comp if t['homeAway'] == 'away')
                    radar.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}", "hora": ev['date'][11:16]
                    })
        except: continue

    print(f"Jogos no radar: {len(radar)}")
    
    # Gera palpites para TODOS os jogos do radar
    candidatos = []
    contador_25 = 0
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    # Seleção de 10 jogos (Se houver mais de 10, busca aproximar Odd 100)
    bilhete_final = []
    if len(candidatos) >= 10:
        # Tenta 1000 combinações para achar a melhor Odd próxima de 100
        melhor_total = 0
        for _ in range(1000):
            teste = random.sample(candidatos, 10)
            o_t = 1.0
            for t in teste: o_t *= t['odd']
            if 80 <= o_t <= 110 and o_t > melhor_total:
                melhor_total = o_t
                bilhete_final = teste
        if not bilhete_final: bilhete_final = candidatos[:10]
    else:
        bilhete_final = candidatos

    if bilhete_final:
        total_odd = 1.0
        for b in bilhete_final: total_odd *= b['odd']
        
        msg = f"🎯 *BILHETE ANALISADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete_final, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        enviar_telegram(msg)
        print(f"Bilhete enviado com {len(bilhete_final)} jogos.")

if __name__ == "__main__":
    executar_robo()
    
