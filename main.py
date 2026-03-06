import os
import requests
import random
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
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

    # ANALISE INDIVIDUAL (O FUNIL)
    s_15_h, s_15_a = calc(evs_h, '1.5'), calc(evs_a, '1.5')
    s_am = max(calc(evs_h, 'ambas'), calc(evs_a, 'ambas'))
    s_25 = max(calc(evs_h, '2.5'), calc(evs_a, '2.5'))
    
    opcoes = []
    # REGRA ANTI-0x0: Exige pelo menos 3/5 de CADA time
    if s_15_h >= 3 and s_15_a >= 3:
        opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": f"{s_15_h}/{s_15_a}"})
    
    if s_am >= 4:
        opcoes.append({"tipo": "AMBOS", "msg": "🎯 Ambas Marcam", "odd": 1.88, "q": f"{s_am}/5"})
    
    if s_25 >= 3:
        opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.15, "q": f"{s_25}/5"})
    
    opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols (HT/FT)", "odd": 1.32, "q": "Segurança"})
    return opcoes

def montar_bilhete(jogos, forcar_fixos=False):
    melhor_b, maior_o = [], 0
    # Simula 1500 combinações para achar a melhor
    for _ in range(1500):
        tentativa, c_25, c_am = [], 0, 0
        qtd = random.randint(6, 10)
        if len(jogos) < qtd: continue
        amostra = random.sample(jogos, qtd)
        
        for j in amostra:
            escolha = j['opcoes'][-1]
            for o in j['opcoes']:
                if forcar_fixos:
                    if o['tipo'] == "2.5" and c_25 < 1: escolha, c_25 = o, c_25 + 1; break
                    if o['tipo'] == "AMBOS" and c_am < 2: escolha, c_am = o, c_am + 1; break
                    if o['tipo'] == "1.5": escolha = o; break
                else:
                    if o['tipo'] == "AMBOS" and c_am < 2: escolha, c_am = o, c_am + 1; break
                    if o['tipo'] == "2.5" and c_25 < 1: escolha, c_25 = o, c_25 + 1; break
                    if o['tipo'] == "1.5": escolha = o; break
            
            tentativa.append({"jogo": j['jogo'], "liga": j['liga'], "hora": j['hora'], "ap": escolha['msg'], "od": escolha['odd'], "qu": escolha['q'], "id_jogo": j['id']})
        
        if forcar_fixos and (c_25 != 1 or c_am != 2): continue
        total_o = 1.0
        for t in tentativa: total_o *= t['od']
        if total_o > maior_o: maior_o, melhor_b = total_o, tentativa
                
    return melhor_b, maior_o

def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    # RADAR GLOBAL (Pega todas as ligas do mundo de uma vez)
    url_global = f"https://site.api.espn.com/apis/site/v2/sports/soccer/scorepanel?dates={hoje}"
    
    jogos_analisados = []
    try:
        res = requests.get(url_global, headers=HEADERS, timeout=15).json()
        for league in res.get('leagues', []):
            l_nome = league.get('name', 'Outra Liga')
            for ev in league.get('events', []):
                if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                    c = ev['competitions'][0]['competitors']
                    j_info = {
                        "id": ev['id'], "liga": l_nome, 
                        "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'], 
                        "hora": ev['date'][11:16],
                        "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}"
                    }
                    j_info['opcoes'] = extrair_probabilidades(j_info)
                    jogos_analisados.append(j_info)
    except: pass

    def formatar_mensagem(titulo, bilhete, odd):
        ligas = sorted(list(set([x['liga'] for x in bilhete])))
        msg = f"{titulo} ({len(bilhete)} JOGOS)\n💰 *ODD TOTAL: {odd:.2f}*\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for liga in ligas: msg += f"🔹 {liga}\n"
        msg += "\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['liga']), 1):
            url_s = f"https://www.espn.com.br/futebol/jogo/_/jogoId/{b['id_jogo']}"
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | {b['liga']}\n🎯 *{b['ap']}* — `[{b['qu']}]` \n📊 [Estatísticas]({url_s})\n\n"
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        return msg

    b1, o1 = montar_bilhete(jogos_analisados, forcar_fixos=False)
    if b1: enviar_telegram(formatar_mensagem("🎯 BILHETE CALIBRADO", b1, o1))

    b2, o2 = montar_bilhete(jogos_analisados, forcar_fixos=True)
    if b2: enviar_telegram(formatar_mensagem("🚀 BILHETE ALAVANCADO", b2, o2))

if __name__ == "__main__":
    executar_robo()
            
