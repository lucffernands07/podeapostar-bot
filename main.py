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

def analisar_partida(j, contador_25):
    """
    Funil de Decisão conforme solicitado:
    Busca 5/5, 4/5, 3/5... até 0/5 (Média)
    """
    l_id = j['liga_id']
    h_id = j['h_id']
    
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

    # 1. Tenta Ambas Marcam (Mínimo 4/5)
    s_am = get_sucessos('ambas')
    if s_am >= 4: return "🎯 Ambas Marcam", 1.82, f"{s_am}/5"

    # 2. Tenta +2.5 (Máximo 1x no bilhete, requer 4/5 ou 5/5)
    if contador_25 < 1:
        s_25 = get_sucessos('2.5')
        if s_25 >= 4: return "🔥 +2.5 Gols", 2.15, f"{s_25}/5"

    # 3. Tenta +1.5 (Escala 5/5, 4/5, 3/5)
    s_15 = get_sucessos('1.5')
    if s_15 >= 3: return "⚽ +1.5 Gols", 1.48, f"{s_15}/5"

    # 4. Fallback 0/5 (Baseado em média ou apenas presença)
    return "🛡️ +0.5 Gols", 1.20, "0/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    # BUSCA GLOBAL: Pega todos os jogos de futebol do mundo de uma vez
    url_global = "http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboards"
    
    radar = []
    try:
        data = requests.get(url_global, timeout=20).json()
        for ev in data.get('events', []):
            if hoje in ev['date']:
                # Extraímos o ID da liga diretamente do evento (evita erro de ID mudado)
                # O ID da liga na ESPN costuma estar em links ou na season
                try:
                    liga_id = ev['links'][0]['href'].split('/')[-3] 
                except:
                    liga_id = ev.get('season', {}).get('slug', 'eng.1')

                comp = ev['competitions'][0]['competitors']
                h = next(t for t in comp if t['homeAway'] == 'home')
                a = next(t for t in comp if t['homeAway'] == 'away')
                
                radar.append({
                    "liga": ev['competitions'][0].get('notes', [{}])[0].get('headline', 'Futebol'),
                    "liga_id": liga_id,
                    "h_id": h['team']['id'],
                    "a_id": a['team']['id'],
                    "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                    "hora": ev['date'][11:16]
                })
    except Exception as e:
        print(f"Erro na varredura: {e}")

    print(f"Total de jogos no radar global: {len(radar)}")

    candidatos = []
    contador_25 = 0
    # Processa TODOS os jogos que encontrou
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    # Seleção Final
    bilhete_final = []
    if len(candidatos) >= 10:
        # Busca a combinação que mais se aproxima de ODD 100
        melhor_total = 0
        for _ in range(2000):
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
        
        msg = f"🎯 *BILHETE VARREDURA TOTAL (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete_final, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        enviar_telegram(msg)
        print(f"Bilhete enviado! {len(bilhete_final)} jogos.")

if __name__ == "__main__":
    executar_robo()
                    
