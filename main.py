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
        total_marcados = 0
        total_sofridos = 0
        jogos_15 = 0
        jogos_25 = 0
        
        for ev in evs:
            try:
                c = ev.get('competitions', [{}])[0].get('competitors', [])
                # Identifica quem é o time atual no histórico
                t_atual = next(t for t in c if str(t['id']) == str(t_id))
                t_rival = next(t for t in c if str(t['id']) != str(t_id))
                
                g_marcados = int(t_atual.get('score', 0))
                g_sofridos = int(t_rival.get('score', 0))
                
                total_marcados += g_marcados
                total_sofridos += g_sofridos
                
                if (g_marcados + g_sofridos) >= 2: jogos_15 += 1
                if (g_marcados + g_sofridos) >= 3: jogos_25 += 1
            except: continue
        return total_marcados, total_sofridos, jogos_15, jogos_25

    m_h, s_h, j15_h, j25_h = analisar_gols(evs_h, j['h_id'])
    m_a, s_a, j15_a, j25_a = analisar_gols(evs_a, j['a_id'])
    
    # --- LOG DE AUDITORIA NO GITHUB ---
    print(f"      📊 {j['jogo']}:")
    print(f"         🏠 Casa: {m_h} Gols Pró / {s_h} Gols Contra | +1.5: {j15_h}/5 | +2.5: {j25_h}/5")
    print(f"         🚀 Fora: {m_a} Gols Pró / {s_a} Gols Contra | +1.5: {j15_a}/5 | +2.5: {j25_a}/5")

    opcoes = []
    # Lógica: Se a soma de gols marcados de um time for > 7 em 5 jogos, ele é um "Atropelador"
    if j15_h >= 3 or j15_a >= 3 or (m_h + m_a) >= 10:
        # Se um time faz muitos gols sozinho, crava o 2.5
        if j25_h >= 4 or j25_a >= 4 or (m_h >= 10 or m_a >= 10):
            opcoes.append({"tipo": "2.5", "msg": "🔥 +2.5 Gols", "odd": 2.15, "q": f"Gols:{m_h}/{m_a}"})
        
        opcoes.append({"tipo": "1.5", "msg": "⚽ +1.5 Gols", "odd": 1.48, "q": f"{j15_h}/{j15_a}"})
    
    opcoes.append({"tipo": "0.5", "msg": "⚡ +0.5 Gols", "odd": 1.32, "q": "Segurança"})
    return opcoes

def montar_bilhete(jogos):
    if not jogos: return [], 0
    # Pega os 8 jogos com mais gols marcados no histórico
    jogos_top = sorted(jogos, key=lambda x: x['opcoes'][0]['q'], reverse=True)[:8]
    
    bilhete = []
    for j in jogos_top:
        escolha = j['opcoes'][0]
        bilhete.append({"jogo": j['jogo'], "liga": j['liga'], "hora": j['hora'], "ap": escolha['msg'], "od": escolha['odd'], "qu": escolha['q'], "id_jogo": j['id']})
    
    total_odd = 1.0
    for b in bilhete: total_odd *= b['od']
    return bilhete, total_odd

def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    print(f"🔎 SCANNER DE ATROPELO: {hoje}")
    
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
                    j_info = {"id": ev['id'], "liga": l_nome, "h_id": c[0]['team']['id'], "a_id": c[1]['team']['id'], "hora": ev['date'][11:16], "jogo": f"{c[0]['team']['displayName']} x {c[1]['team']['displayName']}"}
                    print(f"   ⏳ Analisando: {j_info['jogo']}")
                    j_info['opcoes'] = extrair_probabilidades(j_info)
                    if len(j_info['opcoes']) > 0:
                        jogos_ok.append(j_info)
        except: continue

    if jogos_ok:
        def formatar(titulo, b, o):
            msg = f"🏆 *{titulo}*\n💰 *ODD: {o:.2f}*\n\n"
            for i, x in enumerate(sorted(b, key=lambda k: k['hora']), 1):
                msg += f"{i}. 🏟️ *{x['jogo']}*\n🎯 {x['ap']} `[{x['qu']}]`\n\n"
            return msg
        
        b1, o1 = montar_bilhete(jogos_ok)
        enviar_telegram(formatar("🎯 BILHETE ATROPELO", b1, o1))
    else:
        print("⚠️ Nenhum jogo passou no critério.")

if __name__ == "__main__":
    executar_robo()
    
