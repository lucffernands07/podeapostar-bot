import os
import requests
import random
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.espn.com.br/futebol/calendario"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

def analisar_opcoes(j):
    h_id, a_id, e_id = j['h_id'], j['a_id'], j['id']
    liga_atual = j['liga'].upper()
    
    def get_sucessos(team_id, mercado):
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={e_id}"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            evs = []
            for t_group in res.get('lastGames', []):
                if str(t_group.get('teamId')) == str(team_id):
                    evs = t_group.get('events', [])[-5:]
                    break
            if not evs:
                url_back = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
                res_back = requests.get(url_back, headers=HEADERS, timeout=10).json()
                evs = [e for e in res_back.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
            if not evs: return None
            s = 0
            for ev in evs:
                c = ev.get('competitions', [{}])[0].get('competitors', [])
                g1, g2 = int(c[0].get('score', 0)), int(c[1].get('score', 0))
                if mercado == '2.5' and (g1+g2) >= 3: s += 1
                elif mercado == '1.5' and (g1+g2) >= 2: s += 1
                elif mercado == 'ambas' and (g1 > 0 and g2 > 0): s += 1
            return s
        except: return None

    s_15_raw = max(get_sucessos(h_id, '1.5') or 0, get_sucessos(a_id, '1.5') or 0)
    s_am_raw = max(get_sucessos(h_id, 'ambas') or 0, get_sucessos(a_id, 'ambas') or 0)

    ligas_gols = ["LALIGA", "BUNDESLIGA", "SERIE A", "LIGUE 1", "PORTUGUÊS", "HOLANDÊS", "GAUCHÃO", "ACREANO"]
    if s_15_raw == 0 and any(x in liga_atual for x in ligas_gols):
        s_15, s_am = 4, 3
        qual = f"{s_15}/5 (Est.)"
    else:
        s_15, s_am = s_15_raw, s_am_raw
        qual = f"{s_15}/5"

    # Criamos o leque de opções para o sorteador escolher depois
    opcoes = []
    if s_am >= 4:
        opcoes.append({"tipo": "AMBOS", "msg": "🎯 Ambas Marcam", "odd": 1.88, "q": qual})
    if s_15 >= 4:
        opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.10, "q": qual})
    if s_15 >= 3:
        opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": qual})
    
    opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols (HT/FT)", "odd": 1.32, "q": "Segurança"})
    return opcoes

def executar_robo():
    agora = datetime.now()
    hoje_api, hoje_f = agora.strftime("%Y%m%d"), agora.strftime("%Y-%m-%d")
    
    ligas_ids = {
        "esp.1": "LALIGA", "ger.1": "Bundesliga", "ita.1": "Serie A", "fra.1": "Ligue 1", 
        "por.1": "Português", "bra.camp.gaucho": "Gauchão", "ned.1": "Holandês", 
        "tur.1": "Turco", "bel.1": "Belga", "bra.camp.acreano": "Acreano"
    }

    radar = []
    for l_id, l_nome in ligas_ids.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje_api}"
            data = requests.get(url, headers=HEADERS, timeout=12).json()
            for ev in data.get('events', []):
                if hoje_f in ev['date']:
                    c = ev['competitions'][0]['competitors']
                    radar.append({
                        "id": ev['id'], "liga": l_nome, "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'],
                        "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}",
                        "hora": ev['date'][11:16]
                    })
        except: continue

    print(f"Jogos no Radar: {len(radar)}")
    
    bilhete_final = []
    melhor_bilhete_ate_agora = []
    maior_odd_achada = 0

    # Tenta 5000 combinações para cravar a Odd 80-100
    for _ in range(5000):
        tentativa = []
        c_25, c_am = 0, 0
        # Pega de 10 a 13 jogos para manter apostas fáceis mas com odd alta
        qtd_jogos = random.randint(10, 13) if len(radar) >= 13 else len(radar)
        amostra = random.sample(radar, qtd_jogos)
        
        for j in amostra:
            opcoes = analisar_opcoes(j)
            escolha = opcoes[-1] # Começa com 0.5 (última da lista)
            
            # Prioridades: 1º Ambos (até 2), 2º +2.5 (até 1), 3º +1.5 (sem limite)
            for o in opcoes:
                if o['tipo'] == "AMBOS" and c_am < 2:
                    escolha = o
                    c_am += 1
                    break
                elif o['tipo'] == "2.5" and c_25 < 1:
                    escolha = o
                    c_25 += 1
                    break
                elif o['tipo'] == "1.5":
                    escolha = o
                    break
            
            tentativa.append({**j, "aposta": escolha['msg'], "odd": escolha['odd'], "qualidade": escolha['q']})
        
        odd_total = 1.0
        for t in tentativa: odd_total *= t['odd']
        
        if 80 <= odd_total <= 110:
            bilhete_final = tentativa
            break
        
        if odd_total > maior_odd_achada:
            maior_odd_achada = odd_total
            melhor_bilhete_ate_agora = tentativa

    # Se não achou na faixa 80-100, manda o melhor que conseguiu
    resultado = bilhete_final if bilhete_final else melhor_bilhete_ate_agora

    if resultado:
        t_odd = 1.0
        for r in resultado: t_odd *= r['odd']
        
        msg = f"🎯 *BILHETE DE ELITE (ODD {t_odd:.2f})*\n"
        msg += f"🔥 *FOCO: ODDS 80-100 (JOGOS FÁCEIS)*\n\n"
        
        for i, b in enumerate(sorted(resultado, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | {b['liga']}\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
    
