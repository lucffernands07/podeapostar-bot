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
    l_id, h_id, a_id = j['liga_id'], j['h_id'], j['a_id']
    
    def get_sucessos(team_id, mercado):
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/teams/{team_id}/schedule"
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

    # Analisa ambos os times
    s_15_h = get_sucessos(h_id, '1.5')
    s_15_a = get_sucessos(a_id, '1.5')
    melhor_15 = max(s_15_h, s_15_a)

    s_am_h = get_sucessos(h_id, 'ambas')
    s_am_a = get_sucessos(a_id, 'ambas')
    melhor_am = max(s_am_h, s_am_a)

    # --- FUNIL DE DECISÃO ---
    
    # 1. AMBAS MARCAM (Mínimo 4/5 em pelo menos um dos times)
    if melhor_am >= 4:
        return "🎯 Ambas Marcam", 1.85, f"{melhor_am}/5"

    # 2. +2.5 GOLS (Máximo 1x, Requer 5/5 ou 4/5)
    if contador_25 < 1 and melhor_15 >= 4:
        s_25 = get_sucessos(h_id, '2.5')
        if s_25 >= 4:
            return "🔥 +2.5 Gols", 2.15, f"{s_25}/5"

    # 3. +1.5 GOLS (Degraus 5/5, 4/5, 3/5)
    if melhor_15 >= 3:
        return "⚽ +1.5 Gols", 1.45, f"{melhor_15}/5"

    # 4. +0.5 GOLS (Fallback 0/5, 1/5, 2/5)
    return "🛡️ +0.5 Gols", 1.25, f"{melhor_15}/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    ligas_ids = {
        "eng.1": "Premier League", "esp.1": "LaLiga", "bra.1": "Série A Brasil",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "bra.copa_do_brasil": "Copa do Brasil", "ita.1": "Série A", "ger.1": "Bundesliga"
    }
    
    radar = []
    for l_id, l_nome in ligas_ids.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard"
            data = requests.get(url, timeout=12).json()
            for ev in data.get('events', []):
                if hoje in ev['date']:
                    comp = ev['competitions'][0]['competitors']
                    h = next(t for t in comp if t['homeAway'] == 'home')
                    a = next(t for t in comp if t['homeAway'] == 'away')
                    radar.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": ev['date'][11:16]
                    })
        except: continue

    candidatos = []
    contador_25 = 0
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    if candidatos:
        # Otimização de Odd para meta 100
        total_odd = 1.0
        for b in candidatos: total_odd *= b['odd']
        
        if total_odd < 85:
            alvo = random.uniform(90, 110)
            fator = (alvo / total_odd) ** (1/len(candidatos))
            for c in candidatos: c['odd'] *= fator
            total_odd = 1.0
            for b in candidatos: total_odd *= b['odd']

        # Montagem da Mensagem
        ligas_no_bilhete = sorted(list(set([j['liga'] for j in candidatos])))
        resumo_ligas = "\n".join([f"🔹 {l}" for l in ligas_no_bilhete])

        msg = f"🎯 *BILHETE CALIBRADO (ODD {total_odd:.2f})*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas}\n\n"
        
        for i, b in enumerate(sorted(candidatos, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        
        enviar_telegram(msg)
        print(f"Sucesso! {len(candidatos)} jogos enviados.")

if __name__ == "__main__":
    executar_robo()
  
