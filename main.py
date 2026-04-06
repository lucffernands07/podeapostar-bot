import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DE SEGURANÇA --- #
BSD_TOKEN = os.getenv('BSD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://sports.bzzoiro.com/api"

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def get_stats_e_historico(team_name):
    """Busca histórico e calcula média real de chutes ao gol."""
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"team": team_name, "date_to": ontem, "status": "finished", "tz": "America/Sao_Paulo"}
    
    chutes_totais, jogos_contados = 0, 0
    historico = []

    try:
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        if res.status_code == 200:
            historico = res.json().get("results", [])[:5]
            for j in historico:
                res_detalhe = requests.get(f"{BASE_URL}/events/{j['id']}/", headers=headers)
                if res_detalhe.status_code == 200:
                    detalhes = res_detalhe.json()
                    stats = detalhes.get("live_stats", {})
                    if stats:
                        lado = "home" if detalhes.get('home_team') == team_name else "away"
                        chutes = stats.get(lado, {}).get("shots_on_target", 0)
                        chutes_totais += chutes
                        jogos_contados += 1
    except: pass
    media_chutes = (chutes_totais / jogos_contados) if jogos_contados > 0 else 4.0
    return historico, media_chutes

def analisar_partida(evento):
    home, away = evento['home_team'], evento['away_team']
    hist_h, med_h = get_stats_e_historico(home)
    hist_a, med_a = get_stats_e_historico(away)
    
    if not hist_h or not hist_a: return None

    # Cálculo Gols 1.5
    def count_gols(jogos):
        return sum(1 for j in jogos if (j.get('home_score', 0) or 0) + (j.get('away_score', 0) or 0) > 1.5)

    g15_h, g15_a = count_gols(hist_h), count_gols(hist_a)
    chance_15 = 0
    if g15_h == 5 and g15_a == 5: chance_15 = 100
    elif (g15_h == 5 and g15_a == 4) or (g15_h == 4 and g15_a == 5): chance_15 = 85
    elif g15_h == 4 and g15_a == 4: chance_15 = 70

    # Análise 1X / 2X
    def get_vitoria_stats(jogos, team_name):
        derrotas = 0
        for j in jogos:
            sou_h = j.get('home_team') == team_name
            h_s, a_s = j.get('home_score', 0) or 0, j.get('away_score', 0) or 0
            if (sou_h and h_s < a_s) or (not sou_h and a_s < h_s): derrotas += 1
        ult = jogos[0]
        sou_h_u = ult.get('home_team') == team_name
        vit_u = (sou_h_u and (ult.get('home_score',0)>ult.get('away_score',0))) or (not sou_h_u and (ult.get('away_score',0)>ult.get('home_score',0)))
        return derrotas, vit_u

    d_h, v_h = get_vitoria_stats(hist_h, home)
    d_a, _ = get_vitoria_stats(hist_a, away)
    mercado = ""
    if d_h <= 1 and v_h and d_a >= 2: mercado = f"1X (Chance {80 if d_h == 0 else 65}%)"
    elif d_a == 0 and d_h >= 2: mercado = f"2X (Chance 90%)"

    return {
        "home": home, "away": away,
        "chance_15": chance_15,
        "vitoria": mercado,
        "escanteio": f"-{med_h + med_a:.1f}"
    }

def realizar_analise():
    hoje = datetime.now().strftime('%Y-%m-%d')
    res = requests.get(f"{BASE_URL}/events/", headers={"Authorization": f"Token {BSD_TOKEN}"}, params={"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"})
    
    if res.status_code == 200:
        jogos = res.json().get("results", [])
        aprovados = []
        for j in jogos[:15]:
            analise = analisar_partida(j)
            if analise: aprovados.append(analise)

        if aprovados:
            # PARTE 1: Jogos e Mercados Principal
            bilhete = "🎯 **BILHETE ESTRATÉGICO H2H**\n\n"
            for i, a in enumerate(aprovados, 1):
                bilhete += f"{i}. 🏟️ **{a['home']} x {a['away']}**\n"
                if a['chance_15'] > 0: bilhete += f"🔶 Gols +1.5 (Chance {a['chance_15']}%)\n"
                if a['vitoria']: bilhete += f"💎 Mercado: {a['vitoria']}\n"
                bilhete += "\n"

            # PARTE 2: Seção de Escanteios Separada
            bilhete += "🚩 **DICAS DE ESCANTEIOS (TODOS OS JOGOS)**\n"
            for a in aprovados:
                bilhete += f"• {a['home']} x {a['away']}: {a['escanteio']}\n"
            
            enviar_telegram(bilhete)

if __name__ == "__main__":
    realizar_analise()
