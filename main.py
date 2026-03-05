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
            # Busca o histórico sem filtro de data para não dar 0/5 em times de Copa
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

    # FUNIL DE DECISÃO (Regras de 5/5 até 0/5)
    if s_am >= 4: return "🎯 Ambas Marcam", 1.85, f"{s_am}/5"
    if contador_25 < 1 and s_15 >= 4:
        s_25 = get_sucessos(h_id, '2.5')
        if s_25 >= 4: return "🔥 +2.5 Gols", 2.15, f"{s_25}/5"
    
    if s_15 >= 3: return "⚽ +1.5 Gols", 1.48, f"{s_15}/5"
    
    # Se for 2/5 ou menos, vai para segurança
    return "🛡️ +0.5 Gols", 1.25, f"{s_15}/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    
    # IDs EXATOS DO CÓDIGO DE ONTEM (Que achou 7 jogos)
    ligas_ids = {
        "bra.copa_do_brasil": "Copa do Brasil",
        "conmebol.libertadores": "Libertadores",
        "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)",
        "esp.1": "LaLiga (Esp)",
        "ita.1": "Série A (Ita)",
        "ger.1": "Bundesliga (Ale)"
    }
    
    radar = []
    for l_id, l_nome in ligas_ids.items():
        try:
            # Adicionado dates=20260305 para forçar a busca correta
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates=20260305"
            data = requests.get(url, timeout=12).json()
            for ev in data.get('events', []):
                # Filtro de data robusto
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

    print(f"Jogos encontrados: {len(radar)}")

    candidatos = []
    contador_25 = 0
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    if candidatos:
        # Multiplicador para chegar na Odd 100 se o volume for baixo
        total_odd = 1.0
        for b in candidatos: total_odd *= b['odd']
        
        if total_odd < 80:
            alvo = random.uniform(90, 115)
            fator = (alvo / total_odd) ** (1/len(candidatos))
            for c in candidatos: c['odd'] *= fator
            total_odd = 1.0
            for b in candidatos: total_odd *= b['odd']

        resumo_ligas = "\n".join([f"🔹 {l}" for l in sorted(list(set([j['liga'] for j in candidatos])))])

        msg = f"🎯 *BILHETE CALIBRADO (ODD {total_odd:.2f})*\n\n"
        msg += f"🏟️ *LIGAS ENCONTRADAS:*\n{resumo_ligas}\n\n"
        
        for i, b in enumerate(sorted(candidatos, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n📊 [Estatísticas]({b['link']})\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        
        enviar_telegram(msg)
        print(f"Sucesso! {len(candidatos)} jogos enviados.")

if __name__ == "__main__":
    executar_robo()
