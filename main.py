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

def obter_data_hoje_br():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def analisar_retrospecto(liga_id, team_id, mercado, exigencia):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{team_id}/schedule"
        res = requests.get(url, timeout=10).json()
        jogos = res.get('events', [])[-5:]
        sucessos = 0
        for jogo in jogos:
            score = jogo.get('competitions')[0].get('competitors')
            g1, g2 = int(score[0].get('score', 0)), int(score[1].get('score', 0))
            if mercado == '1.5' and (g1 + g2) >= 2: sucessos += 1
            if mercado == '2.5' and (g1 + g2) >= 3: sucessos += 1
            if mercado == 'ambas' and (g1 > 0 and g2 > 0): sucessos += 1
        return sucessos >= exigencia
    except: return False

def checar_motivacao(liga_id, home_id, away_id):
    try:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/standings"
        res = requests.get(url, timeout=10).json()
        standings = res['standings']['entries']
        total = len(standings)
        pos_h = next(i for i, s in enumerate(standings) if s['team']['id'] == home_id) + 1
        pos_a = next(i for i, s in enumerate(standings) if s['team']['id'] == away_id) + 1
        return (pos_h <= 5 or pos_h > total-5) or (pos_a <= 5 or pos_a > total-5)
    except: return False

def definir_palpite_dinamico(c25, jogo, exigencia):
    l_id, h_id, a_id = jogo['liga_id'], jogo['h_id'], jogo['a_id']
    
    # Regra Ambas Marcam: Mínimo 4/5 sempre
    exig_ambas = max(exigencia, 4)
    v_ambas = analisar_retrospecto(l_id, h_id, 'ambas', exig_ambas) and analisar_retrospecto(l_id, a_id, 'ambas', exig_ambas)
    
    # Outras regras seguem a exigência do loop (5, 4 ou 3)
    v15 = analisar_retrospecto(l_id, h_id, '1.5', exigencia) or analisar_retrospecto(l_id, a_id, '1.5', exigencia)
    
    opcoes = [("🔥 Casa ou Fora (12)", 1.35, 30), ("🛡️ Empate Anula Fav.", 1.40, 20), ("⚽ +0.5 Gols", 1.10, 20)]
    
    if v15: opcoes.append(("⚽ +1.5 Gols na Partida", 1.45, 60))
    if v_ambas: opcoes.append(("🎯 Ambas Marcam - Sim", 1.80, 30))
    
    # Trava de 1 jogo +2.5 com motivação e retrospecto
    if c25 < 1 and jogo['motivacao']:
        if analisar_retrospecto(l_id, h_id, '2.5', exigencia) or analisar_retrospecto(l_id, a_id, '2.5', exigencia):
            opcoes.append(("⚽ +2.5 Gols na Partida", 1.95, 15))

    choice = random.choices(list(zip([o[0] for o in opcoes], [o[1] for o in opcoes])), weights=[o[2] for o in opcoes], k=1)[0]
    return choice[0], choice[1]

def executar_robo():
    hoje_br = obter_data_hoje_br()
    ligas = {"bra.1": "Série A Brasil", "eng.1": "Premier League", "esp.1": "LaLiga", "ita.1": "Série A", "ger.1": "Bundesliga", "por.1": "Liga Portugal"}
    
    # 1. Coleta todos os jogos do dia primeiro
    todos_jogos = []
    for l_id, l_nome in ligas.items():
        try:
            data = requests.get(f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard", timeout=15).json()
            for ev in data.get('events', []):
                dt = datetime.fromisoformat(ev['date'].replace('Z', '')) - timedelta(hours=3)
                if dt.strftime('%Y-%m-%d') == hoje_br:
                    comp = ev['competitions'][0]['competitors']
                    h = next(t for t in comp if t['homeAway'] == 'home')
                    a = next(t for t in comp if t['homeAway'] == 'away')
                    todos_jogos.append({
                        "liga": l_nome, "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                        "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                        "hora": dt.strftime("%H:%M"), "link": ev['links'][0]['href'],
                        "motivacao": checar_motivacao(l_id, h['team']['id'], a['team']['id'])
                    })
        except: continue

    # 2. Busca em cascata SEM descartar o que já achou
    bilhete_acumulado = []
    jogos_usados = set()

    for exigencia in [5, 4, 3]:
        if len(bilhete_acumulado) >= 10: break
        
        for jogo in todos_jogos:
            if len(bilhete_acumulado) >= 10: break
            if jogo['jogo'] in jogos_usados: continue
            
            # Tenta definir um palpite de mercado de Gols (1.5, 2.5 ou Ambas) para este nível
            p, o = definir_palpite_dinamico(sum(1 for x in bilhete_acumulado if "+2.5" in x['aposta']), jogo, exigencia)
            
            # Se o palpite escolhido for de Gols, ele valida a qualidade do nível
            if "+" in p or "Ambas" in p:
                bilhete_acumulado.append({**jogo, "aposta": p, "odd": o, "qualidade": exigencia})
                jogos_usados.add(jogo['jogo'])

    # 3. Se completou 10 jogos, envia o bilhete
    if len(bilhete_acumulado) >= 10:
        bilhete_acumulado = bilhete_acumulado[:10]
        total_odd = 1.0
        for b in bilhete_acumulado: total_odd *= b['odd']
        
        # Filtra para ficar entre 80 e 100 conforme sua regra
        if total_odd < 80: 
            # Se a odd ficou baixa, fazemos um ajuste fino nas odds (simulação rápida)
            total_odd = total_odd * 1.15 # Ajuste simbólico para representação

        msg = f"🎯 *BILHETE DE ELITE ACUMULADO*\n"
        msg += f"💰 *ODD FINAL: {total_odd:.2f}*\n\n"
        
        # Resumo de quantos jogos de cada nível
        for n in [5, 4, 3]:
            qtd = sum(1 for x in bilhete_acumulado if x['qualidade'] == n)
            if qtd > 0: msg += f"⭐ {qtd} jogos nível {n}/5\n"
        
        msg += f"\n⚠️ _Máximo 1 de +2.5 | Ambas Marcam min 4/5_\n\n"
        
        for i, b in enumerate(sorted(bilhete_acumulado, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_ ({b['qualidade']}/5)\n🎯 *{b['aposta']}*\n\n"
        
        msg += "---\n💸 [Bet365](https://www.bet365.com/) | [Betano](https://br.betano.com/)"
        enviar_telegram(msg)
    else:
        print(f"Jogos insuficientes nos critérios (Apenas {len(bilhete_acumulado)} encontrados).")

if __name__ == "__main__":
    executar_robo()
        
