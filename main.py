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
    try: 
        requests.post(url, json=payload, timeout=15)
        print("   ✅ Notificação enviada ao Telegram.")
    except: 
        print("   ❌ Erro ao enviar para o Telegram.")

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
    
    if not evs_h or not evs_a: return []

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

    s_15_h, s_15_a = calc(evs_h, '1.5'), calc(evs_a, '1.5')
    s_am_h, s_am_a = calc(evs_h, 'ambas'), calc(evs_a, 'ambas')
    s_25_h, s_25_a = calc(evs_h, '2.5'), calc(evs_a, '2.5')
    
    opcoes = []
    
    # --- LÓGICA DE ATROPELO (Barcelona Rule) ---
    
    # 1. MERCADO +1.5 GOLS: Aceita se um for 5/5 OU se a soma for >= 7
    if s_15_h == 5 or s_15_a == 5 or (s_15_h + s_15_a) >= 7:
        opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": f"{s_15_h}/{s_15_a}"})

    # 2. AMBAS MARCAM: Aceita se um for 4/5 OU se a soma for >= 7
    if s_am_h >= 4 or s_am_a >= 4 or (s_am_h + s_am_a) >= 7:
        opcoes.append({"tipo": "AMBOS", "msg": "🎯 Ambas Marcam", "odd": 1.88, "q": f"{s_am_h}/{s_am_a}"})
    
    # 3. +2.5 GOLS: Aceita se um for 5/5 OU se a soma for >= 8
    if s_25_h == 5 or s_25_a == 5 or (s_25_h + s_25_a) >= 8:
        opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.15, "q": f"{s_25_h}/{s_25_a}"})
    
    opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols", "odd": 1.32, "q": "Segurança"})
    return opcoes

def montar_bilhete(jogos, forcar_fixos=False):
    melhor_b, maior_o = [], 0
    if not jogos: return melhor_b, maior_o
    for _ in range(2000):
        tentativa, c_25, c_am = [], 0, 0
        amostra = random.sample(jogos, min(len(jogos), random.randint(6, 10)))
        for j in amostra:
            opcs = {o['tipo']: o for o in j['opcoes']}
            escolha = j['opcoes'][-1] # Default Segurança
            
            if forcar_fixos:
                # Regra para o Alavancado
                if '2.5' in opcs and c_25 < 1: escolha, c_25 = opcs['2.5'], c_25 + 1
                elif 'AMBOS' in opcs and c_am < 2: escolha, c_am = opcs['AMBOS'], c_am + 1
                elif '1.5' in opcs: escolha = opcs['1.5']
            else:
                # No Calibrado: Prioriza 2.5 se tiver um time 5/5, senão vai de 1.5
                if '2.5' in opcs and '5/' in opcs['2.5']['q']: escolha = opcs['2.5']
                elif '1.5' in opcs: escolha = opcs['1.5']
                
            tentativa.append({"jogo": j['jogo'], "liga": j['liga'], "hora": j['hora'], "ap": escolha['msg'], "od": escolha['odd'], "qu": escolha['q'], "id_jogo": j['id']})
        
        total_o = 1.0
        for t in tentativa: total_o *= t['od']
        if total_o > maior_o: maior_o, melhor_b = total_o, tentativa
    return melhor_b, maior_o

def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    print(f"🔎 BUSCANDO JOGOS PARA A DATA: {hoje}")
    print("-" * 50)
    
    ligas_alvo = {
        "eng.1": "Premier League", "esp.1": "LALIGA", "ger.1": "Bundesliga", 
        "ita.1": "Serie A", "fra.1": "Ligue 1", "por.1": "Português", 
        "ned.1": "Holandês", "tur.1": "Turco", "bra.libertadores": "Libertadores",
        "bra.sudamericana": "Sul-Americana", "bra.camp.paulista": "Paulistão",
        "bra.camp.carioca": "Carioca", "bra.camp.mineiro": "Mineiro", "bra.camp.gaucho": "Gauchão"
    }

    jogos_analisados = []
    
    for l_id, l_nome in ligas_alvo.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            eventos = res.get('events', [])
            
            print(f" League: {l_nome} ({l_id})")
            
            if not eventos:
                print("   ❌ Nenhum jogo encontrado nesta liga.")
            
            for ev in eventos:
                status = ev.get('status', {}).get('type', {}).get('state')
                if status == 'pre':
                    c = ev['competitions'][0]['competitors']
                    j_info = {
                        "id": ev['id'], "liga": l_nome, 
                        "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'], 
                        "hora": ev['date'][11:16],
                        "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}"
                    }
                    print(f"   ⏳ Analisando: [{j_info['hora']}] {j_info['jogo']}")
                    j_info['opcoes'] = extrair_probabilidades(j_info)
                    
                    if len(j_info['opcoes']) > 1:
                        jogos_analisados.append(j_info)
        except: continue
        print("-" * 50)

    print(f"\n✅ ANÁLISE CONCLUÍDA. {len(jogos_analisados)} jogos aprovados pelo funil.")
    
    if not jogos_analisados:
        print("⚠️ Fim do script: Nenhum jogo atingiu os critérios.")
        return

    def formatar(titulo, bilhete, odd):
        msg = f"🏆 *{titulo}*\n💰 *ODD TOTAL: {odd:.2f}*\n\n"
        for i, b in enumerate(sorted(bilhete, key=lambda x: x['hora']), 1):
            url_s = f"https://www.espn.com.br/futebol/jogo/_/jogoId/{b['id_jogo']}"
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | {b['liga']}\n🎯 *{b['ap']}* — `[{b['qu']}]` \n📊 [Estatísticas]({url_s})\n\n"
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        return msg

    b1, o1 = montar_bilhete(jogos_analisados, False)
    if b1: enviar_telegram(formatar("🎯 BILHETE CALIBRADO", b1, o1))

    b2, o2 = montar_bilhete(jogos_analisados, True)
    if b2: enviar_telegram(formatar("🚀 BILHETE ALAVANCADO", b2, o2))

if __name__ == "__main__":
    executar_robo()
    
