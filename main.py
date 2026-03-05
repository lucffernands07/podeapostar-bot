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
    l_id, h_id = j['liga_id'], j['h_id']
    
    def get_sucessos(mercado):
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/teams/{h_id}/schedule"
            res = requests.get(url, timeout=8).json()
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

    # FUNIL DE ANÁLISE DESCENDENTE
    # 1. Ambas Marcam (Prio: 5/5, 4/5)
    s_am = get_sucessos('ambas')
    if s_am >= 4: return "🎯 Ambas Marcam", 1.85, f"{s_am}/5"

    # 2. +2.5 Gols (Máximo 1x no bilhete, Prio: 5/5, 4/5)
    if contador_25 < 1:
        s_25 = get_sucessos('2.5')
        if s_25 >= 4: return "🔥 +2.5 Gols", 2.10, f"{s_25}/5"

    # 3. +1.5 Gols (Prio: 5/5 -> 4/5 -> 3/5)
    for n in [5, 4, 3]:
        s_15 = get_sucessos('1.5')
        if s_15 >= n: return "⚽ +1.5 Gols", 1.45, f"{n}/5"

    # 4. +0.5 Gols (Fallback 0/5 - Baseado em "Gols Pro/Contra" ou Presença)
    return "🛡️ +0.5 Gols", 1.18, "0/5 (Média)"

def executar_robo():
    hoje = "2026-03-05"
    print(f"--- INICIANDO VARREDURA TRIPLA PARA {hoje} ---")
    
    # Método 1: IDs de Ligas Estáveis (Baseado no seu código de ontem)
    ligas_ids = ["eng.1", "esp.1", "bra.1", "ita.1", "ger.1", "conmebol.libertadores", "conmebol.sudamericana", "bra.copa_do_brasil"]
    
    radar = []
    
    # Tenta buscar jogo por jogo nas ligas conhecidas primeiro
    for l_id in ligas_ids:
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates=20260305"
            data = requests.get(url, timeout=10).json()
            for ev in data.get('events', []):
                comp = ev['competitions'][0]['competitors']
                h = next(t for t in comp if t['homeAway'] == 'home')
                a = next(t for t in comp if t['homeAway'] == 'away')
                radar.append({
                    "liga_id": l_id, "h_id": h['team']['id'], "a_id": a['team']['id'],
                    "jogo": f"{h['team']['displayName']} x {a['team']['displayName']}",
                    "hora": ev['date'][11:16], "liga": l_id
                })
        except: continue

    print(f"Jogos encontrados no radar: {len(radar)}")

    # Processamento e Montagem do Bilhete
    candidatos = []
    contador_25 = 0
    for j in radar:
        aposta, odd, qual = analisar_partida(j, contador_25)
        if "+2.5" in aposta: contador_25 += 1
        candidatos.append({**j, "aposta": aposta, "odd": odd, "qualidade": qual})

    # Se houver jogos, envia o bilhete (mesmo que seja 1 ou 15)
    if candidatos:
        # Se passar de 10, tenta otimizar a Odd para perto de 100
        if len(candidatos) > 10:
            melhor_o = 0
            final = []
            for _ in range(500):
                teste = random.sample(candidatos, 10)
                o_t = 1.0
                for t in teste: o_t *= t['odd']
                if 80 <= o_t <= 120 and o_t > melhor_o:
                    melhor_o = o_t
                    final = teste
            bilhete_exibir = final if final else candidatos[:10]
        else:
            bilhete_exibir = candidatos

        total_odd = 1.0
        for b in bilhete_exibir: total_odd *= b['odd']

        msg = f"🎯 *BILHETE ANALISADO (ODD {total_odd:.2f})*\n\n"
        for i, b in enumerate(sorted(bilhete_exibir, key=lambda x: x['liga']), 1):
            msg += f"{i}. 🏟️ *{b['jogo']}*\n🕒 {b['hora']} | _{b['liga']}_\n🎯 *{b['aposta']}* — `[{b['qualidade']}]` \n\n"
        
        enviar_telegram(msg)
        print("Bilhete enviado!")
    else:
        print("Nenhum jogo encontrado. Verifique se a data da ESPN para hoje está ativa.")

if __name__ == "__main__":
    executar_robo()

