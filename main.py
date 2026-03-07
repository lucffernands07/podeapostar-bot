import os
import requests
import random
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try: requests.post(url, json=payload, timeout=15)
    except: print("   ❌ Erro Telegram.")

def get_historico_stats(e_id, team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={e_id}"
        res = requests.get(url, headers=HEADERS, timeout=7).json()
        for t_group in res.get('lastGames', []):
            if str(t_group.get('teamId')) == str(team_id):
                return t_group.get('events', [])[-5:]
        return []
    except: return []

def extrair_probabilidades(j):
    evs_h = get_historico_stats(j['id'], j['h_id'])
    evs_a = get_historico_stats(j['id'], j['a_id'])
    
    def analisar_gols(evs, t_id):
        m, s, j15, j25 = 0, 0, 0, 0
        for ev in evs:
            try:
                c = ev.get('competitions', [{}])[0].get('competitors', [])
                t_at = next(t for t in c if str(t['id']) == str(t_id))
                t_ri = next(t for t in c if str(t['id']) != str(t_id))
                gm, gs = int(t_at.get('score', 0)), int(t_ri.get('score', 0))
                m += gm; s += gs
                if (gm + gs) >= 2: j15 += 1
                if (gm + gs) >= 3: j25 += 1
            except: continue
        return m, s, j15, j25

    m_h, s_h, j15_h, j25_h = analisar_gols(evs_h, j['h_id'])
    m_a, s_a, j15_a, j25_a = analisar_gols(evs_a, j['a_id'])
    
    # Log no GitHub para conferirmos os números reais do Barça no log
    print(f"      📊 {j['jogo']}: Casa {m_h}G ({j25_h}/5 Over 2.5) | Fora {m_a}G ({j25_a}/5 Over 2.5)")

    opcoes = []
    
    # 1. TENTATIVA +2.5 GOLS (SE UM TIME FOR MÁQUINA OU A SOMA FOR ALTA)
    if j25_h >= 4 or j25_a >= 4 or m_h >= 8 or m_a >= 8 or (m_h + m_a) >= 12:
        opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.15, "q": f"V:{m_h+m_a}"})
    
    # 2. TENTATIVA +1.5 GOLS (CRITÉRIO MÍNIMO PARA TIMES COMO BARCELONA)
    if j15_h >= 2 or j15_a >= 2 or (m_h + m_a) >= 6:
        opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": f"{j15_h}/{j15_a}"})
    
    # 3. SEGURANÇA (SÓ SE OS TIMES FOREM EXTREMAMENTE RUINS)
    if not opcoes:
        opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols", "odd": 1.32, "q": "Segur."})
        
    return opcoes

def montar_bilhete(jogos):
    if not jogos: return [], 0
    # ORDENAÇÃO: Prioriza quem tem a opção 2.5 disponível
    jogos_ordenados = sorted(jogos, key=lambda x: (x['opcoes'][0]['tipo'] == "2.5"), reverse=True)
    
    bilhete = []
    for j in jogos_ordenados[:10]:
        escolha = j['opcoes'][0] # Pega a mais agressiva (2.5 ou 1.5)
        bilhete.append({"jogo": j['jogo'], "ap": escolha['msg'], "od": escolha['odd'], "qu": escolha['q'], "hora": j['hora']})
    
    total_odd = 1.0
    for b in bilhete: total_odd *= b['od']
    return bilhete, total_odd

def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    print(f"🔎 BUSCA MODO GOLEADA: {hoje}")
    
    ligas = {
        "eng.1": "Premier League", "esp.1": "LALIGA", "ger.1": "Bundesliga", 
        "ita.1": "Serie A", "fra.1": "Ligue 1", "por.1": "Português", 
        "ned.1": "Holandês", "tur.1": "Turco", "bra.camp.paulista": "Paulistão",
        "bra.camp.carioca": "Carioca", "bra.camp.gaucho": "Gauchão"
    }

    jogos_ok = []
    for l_id, l_nome in ligas.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            for ev in res.get('events', []):
                if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                    c = ev['competitions'][0]['competitors']
                    j_info = {"id": ev['id'], "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'], "hora": ev['date'][11:16], "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}"}
                    print(f"   ⏳ Analisando: {j_info['jogo']}")
                    j_info['opcoes'] = extrair_probabilidades(j_info)
                    if j_info['opcoes']:
                        jogos_ok.append(j_info)
        except: continue

    if jogos_ok:
        b, o = montar_bilhete(jogos_ok)
        msg = f"🏆 *🎯 BILHETE ATROPELO GOLEADA*\n💰 *ODD: {o:.2f}*\n\n"
        for i, x in enumerate(sorted(b, key=lambda k: k['hora']), 1):
            msg += f"{i}. 🏟️ *{x['jogo']}*\n🎯 *{x['ap']}* `[{x['qu']}]`\n\n"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
                
