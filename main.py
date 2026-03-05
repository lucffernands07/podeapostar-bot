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

    s_15 = max(get_sucessos(h_id, '1.5'), get_sucessos(a_id, '1.5'))
    s_am = max(get_sucessos(h_id, 'ambas'), get_sucessos(a_id, 'ambas'))

    # 1. Ambas Marcam (Mínimo 4/5 conforme sua regra)
    if s_am >= 4: 
        return "🎯 Ambas Marcam", 1.85, f"{s_am}/5"
    
    # 2. +2.5 Gols (Máximo 1x no bilhete)
    if contador_25 < 1 and s_15 >= 4:
        s_25 = get_sucessos(h_id, '2.5')
        if s_25 >= 4: return "🔥 +2.5 Gols", 2.15, f"{s_25}/5"
    
    # 3. +1.5 Gols (Foco estatístico 3/5 a 5/5)
    if s_15 >= 3: 
        return "⚽ +1.5 Gols", 1.48, f"{s_15}/5"
    
    # 4. +0.5 Gols HT/FT (Critério de Segurança para volume)
    return "⚡ +0.5 Gols (HT/FT)", 1.38, f"{s_15}/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    
    # IDs ATUALIZADOS CONFORME SUAS URLs MANUAIS
    ligas_ids = {
        "bra.copa_do_brazil": "Copa do Brasil",
        "conmebol.libertadores": "Libertadores",
        "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)",
        "esp.1": "LaLiga (Esp)",
        "ita.1": "Série A (Ita)",
        "ger.1": "Bundesliga (Ale)"
    }

    # Scanner dinâmico para capturar qualquer outro ID que mude
    try:
        url_scan = "http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboards"
        data_scan = requests.get(url_scan, timeout=10).json()
        for ev in data_scan.get('events', []):
            try:
                slug = ev['league']['slug']
                nome = ev['league']['name']
                if slug not in ligas_ids:
                    ligas_ids[slug] = nome
            except: continue
    except: print("Aviso: Scanner Global indisponível.")

    radar = []
    for l_id, l_nome in ligas_ids.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates=20260305"
            data = requests.get(url, timeout=12).json()
            for ev in data.get('events', []):
                if hoje in ev['date']:
                    comp = ev['competitions'][0]['competitors']
                    h = next(t for t in comp if t['homeAway'] == 'home')
                    a = next(t for t in comp if t['homeAway'] == 'away')
                    radar.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": ev['date'][11:16],
                        "link": ev['links'][0]['href']
                    })
        except: continue

    print(f"Jogos encontrados no radar: {len(radar)}")

    candidatos = []
    contador_25 = 0
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    # SELEÇÃO INTELIGENTE (7 A 10 JOGOS)
    final_escolhidos = []
    if len(candidatos) > 10:
        melhor_distancia = float('inf')
        for _ in range(1000):
            amostra = random.sample(candidatos, 10)
            odd_temp = 1.0
            for a in amostra: odd_temp *= a['odd']
            distancia = abs(odd_temp - 100)
            if distancia < melhor_distancia:
                melhor_distancia = distancia
                final_escolhidos = amostra
    else:
        final_escolhidos = candidatos

    # ENVIO (Requisito: Mínimo de 7 jogos)
    if len(final_escolhidos) >= 7:
        total_odd = 1.0
        for b in final_escolhidos: total_odd *= b['odd']

        resumo_ligas = "\n".join([f"🔹 {l}" for l in sorted(list(set([j['liga'] for j in final_escolhidos])))])

        msg = f"🎯 *BILHETE ANALISADO ({len(final_escolhidos)} JOGOS)*\n"
        msg += f"💰 *ODD TOTAL: {total_odd:.2f}*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas}\n\n"
        
        for i, b in enumerate(sorted(final_escolhidos, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n📊 [Estatísticas]({b['link']})\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        
        enviar_telegram(msg)
        print(f"Sucesso! Bilhete com {len(final_escolhidos)} jogos enviado.")
    else:
        print(f"Volume insuficiente: {len(final_escolhidos)} jogos encontrados. Mínimo é 7.")

if __name__ == "__main__":
    executar_robo()
                
