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

def get_historico_stats(e_id, team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={e_id}"
        res = requests.get(url, headers=HEADERS, timeout=7).json()
        evs = []
        for t_group in res.get('lastGames', []):
            if str(t_group.get('teamId')) == str(team_id):
                evs = t_group.get('events', [])[-5:]
                break
        if not evs:
            url_back = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
            res_back = requests.get(url_back, headers=HEADERS, timeout=7).json()
            evs = [e for e in res_back.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
        return evs
    except: return []

def extrair_probabilidades(j):
    evs_h = get_historico_stats(j['id'], j['h_id'])
    evs_a = get_historico_stats(j['id'], j['a_id'])
    
    def calc(evs, mercado):
        s = 0
        for ev in evs:
            try:
                c = ev.get('competitions', [{}])[0].get('competitors', [])
                g1, g2 = int(c[0].get('score', 0)), int(c[1].get('score', 0))
                if mercado == '2.5' and (g1+g2) >= 3: s += 1
                elif mercado == '1.5' and (g1+g2) >= 2: s += 1
                elif mercado == 'ambas' and (g1 > 0 and g2 > 0): s += 1
            except: continue
        return s

    s_15 = max(calc(evs_h, '1.5'), calc(evs_a, '1.5'))
    s_am = max(calc(evs_h, 'ambas'), calc(evs_a, 'ambas'))
    s_25 = max(calc(evs_h, '2.5'), calc(evs_a, '2.5'))
    
    liga_atual = j['liga'].upper()
    ligas_gols = ["LALIGA", "BUNDESLIGA", "SERIE A", "LIGUE 1", "PORTUGUÊS", "HOLANDÊS", "GAUCHÃO", "ACREANO"]
    
    if s_15 == 0 and any(x in liga_atual for x in ligas_gols):
        s_15, s_am, s_25 = 4, 3, 2
        qual = f"{s_15}/5 (Est.)"
    else:
        qual = f"{s_15}/5"

    opcoes = []
    if s_15 >= 3: opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": qual})
    if s_am >= 4: opcoes.append({"tipo": "AMBOS", "msg": "🎯 Ambas Marcam", "odd": 1.88, "q": f"{s_am}/5"})
    if s_25 >= 3: opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.15, "q": f"{s_25}/5"})
    opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols (HT/FT)", "odd": 1.32, "q": "Segurança"})
    return opcoes

def montar_bilhete(jogos, forcar_fixos=False):
    melhor_b = []
    maior_o = 0
    for _ in range(1000):
        tentativa = []
        c_25, c_am = 0, 0
        qtd = random.randint(5, 10)
        amostra = random.sample(jogos, min(len(jogos), qtd))
        
        for j in amostra:
            escolha = j['opcoes'][-1]
            for o in j['opcoes']:
                if forcar_fixos:
                    if o['tipo'] == "2.5" and c_25 < 1:
                        escolha, c_25 = o, c_25 + 1; break
                    if o['tipo'] == "AMBOS" and c_am < 2:
                        escolha, c_am = o, c_am + 1; break
                    if o['tipo'] == "1.5": escolha = o; break
                else:
                    if o['tipo'] == "AMBOS" and c_am < 2: escolha, c_am = o, c_am + 1; break
                    if o['tipo'] == "2.5" and c_25 < 1: escolha, c_25 = o, c_25 + 1; break
                    if o['tipo'] == "1.5": escolha = o; break
            
            tentativa.append({
                "jogo": j['jogo'], "liga": j['liga'], "hora": j['hora'], 
                "ap": escolha['msg'], "od": escolha['odd'], "qu": escolha['q']
            })
        
        if forcar_fixos and (c_25 != 1 or c_am != 2): continue

        total_o = 1.0
        for t in tentativa: total_o *= t['od']
        if total_o > maior_o:
            maior_o, melhor_b = total_o, tentativa
                
    return melhor_b, maior_o

def executar_robo():
    agora = datetime.now()
    hoje_api, hoje_f = agora.strftime("%Y%m%d"), agora.strftime("%Y-%m-%d")
    ligas_ids = {"esp.1": "LALIGA", "ger.1": "Bundesliga", "ita.1": "Serie A", "fra.1": "Ligue 1", "por.1": "Português", "bra.camp.gaucho": "Gauchão", "ned.1": "Holandês", "tur.1": "Turco", "bel.1": "Belga", "bra.camp.acreano": "Acreano"}

    radar_bruto = []
    for l_id, l_nome in ligas_ids.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje_api}"
            data = requests.get(url, headers=HEADERS, timeout=12).json()
            for ev in data.get('events', []):
                if hoje_f in ev['date']:
                    c = ev['competitions'][0]['competitors']
                    radar_bruto.append({"id": ev['id'], "liga": l_nome, "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'], "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}", "hora": ev['date'][11:16]})
        except: continue

    jogos_analisados = []
    for j in radar_bruto:
        opcoes = extrair_probabilidades(j)
        jogos_analisados.append({**j, "opcoes": opcoes})

    def formatar_mensagem(titulo, bilhete, odd):
        ligas = sorted(list(set([x['liga'] for x in bilhete])))
        msg = f"{titulo} ({len(bilhete)} JOGOS)\n💰 *ODD TOTAL: {odd:.2f}*\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for liga in ligas: msg += f"🔹 {liga}\n"
        msg += "\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | {b['liga']}\n🎯 *{b['ap']}* — `[{b['qu']}]` \n📊 Estatísticas\n\n"
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        return msg

    # BILHETE 01
    b1, o1 = montar_bilhete(jogos_analisados, forcar_fixos=False)
    if b1: enviar_telegram(formatar_mensagem("🎯 BILHETE CALIBRADO", b1, o1))

    # BILHETE 02
    b2, o2 = montar_bilhete(jogos_analisados, forcar_fixos=True)
    if b2: enviar_telegram(formatar_mensagem("🚀 BILHETE ALAVANCADO", b2, o2))

if __name__ == "__main__":
    executar_robo()
    
