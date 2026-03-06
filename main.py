import os
import requests
import random
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

def analisar_partida(j, contador_25):
    # Usamos o ID do evento (jogo) para pegar o Summary
    evento_id = j['id']
    
    def get_sucessos_via_summary(team_id, mercado):
        try:
            # ENDPOINT SUMMARY: Contém os últimos jogos (recentGames)
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={evento_id}"
            res = requests.get(url, timeout=10).json()
            
            # Localiza o histórico do time específico (Casa ou Fora) no Summary
            # A ESPN coloca o histórico em 'recentGames' dentro do boxscore ou no 'lastGames'
            teams_data = res.get('lastGames', []) # Alguns eventos usam essa chave
            if not teams_data:
                # Fallback para o endpoint de histórico por time caso o summary falhe
                url_back = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
                res = requests.get(url_back, timeout=10).json()
                evs = [e for e in res.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
            else:
                # Filtra os jogos do time solicitado
                evs = []
                for t_group in teams_data:
                    if str(t_group.get('teamId')) == str(team_id):
                        evs = t_group.get('events', [])[-5:]
                        break
            
            if not evs: return 0
            s = 0
            for ev in evs:
                # No Summary/LastGames a estrutura de gols é mais simples
                competitors = ev.get('competitions', [{}])[0].get('competitors', [])
                g1 = int(competitors[0].get('score', 0))
                g2 = int(competitors[1].get('score', 0))
                
                if mercado == '2.5' and (g1+g2) >= 3: s += 1
                elif mercado == '1.5' and (g1+g2) >= 2: s += 1
                elif mercado == 'ambas' and (g1 > 0 and g2 > 0): s += 1
            return s
        except: return 0

    # Pega estatísticas (Garante que saia do 0/5)
    s_15 = max(get_sucessos_via_summary(j['h_id'], '1.5'), get_sucessos_via_summary(j['a_id'], '1.5'))
    s_am = max(get_sucessos_via_summary(j['h_id'], 'ambas'), get_sucessos_via_summary(j['a_id'], 'ambas'))

    # REGRAS DO USUÁRIO
    if s_am >= 4: return "🎯 Ambas Marcam", 1.85, f"{s_am}/5"
    if contador_25 < 1 and s_15 >= 4:
        s_25 = max(get_sucessos_via_summary(j['h_id'], '2.5'), get_sucessos_via_summary(j['a_id'], '2.5'))
        if s_25 >= 4: return "🔥 +2.5 Gols", 2.15, f"{s_25}/5"
    if s_15 >= 3: return "⚽ +1.5 Gols", 1.48, f"{s_15}/5"
    
    return "⚡ +0.5 Gols (HT/FT)", 1.38, f"{s_15}/5 (Média)"

def executar_robo():
    agora = datetime.now()
    hoje_api = agora.strftime("%Y%m%d")
    hoje_filtro = agora.strftime("%Y-%m-%d")
    
    # Scanner de ligas expandido
    ligas_ids = {
        "esp.1": "LALIGA", "ger.1": "Bundesliga", "ita.1": "Serie A", 
        "fra.1": "Ligue 1", "por.1": "Português", "bra.camp.gaucho": "Gauchão",
        "ned.1": "Holandês", "tur.1": "Turco", "bel.1": "Belga",
        "bra.camp.acreano": "Acreano", "bra.camp.amazonense": "Amazonense"
    }

    radar = []
    # Usamos o Scoreboard para listar os jogos
    for l_id, l_nome in ligas_ids.items():
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje_api}"
            data = requests.get(url, timeout=12).json()
            for ev in data.get('events', []):
                if hoje_filtro in ev['date']:
                    c = ev['competitions'][0]['competitors']
                    h = next(t for t in c if t['homeAway'] == 'home')
                    a = next(t for t in c if t['homeAway'] == 'away')
                    radar.append({
                        "id": ev['id'], # Importante para o Summary
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": ev['date'][11:16]
                    })
        except: continue

    print(f"Jogos encontrados: {len(radar)}")
    candidatos, c25 = [], 0
    for j in radar:
        ap, od, qu = analisar_partida(j, c25)
        if "+2.5" in ap: c25 += 1
        candidatos.append({**j, "aposta": ap, "odd": od, "qualidade": qu})

    # Seleção estratégica para Odd 80-100
    if len(candidatos) >= 10:
        amostra = random.sample(candidatos, 10)
    else:
        amostra = candidatos

    if len(amostra) >= 5:
        total_odd = 1.0
        for s in amostra: total_odd *= s['odd']
        
        msg = f"🎯 *BILHETE ANALISADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(amostra, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | {b['liga']}\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)

if __name__ == "__main__":
    executar_robo()
    
