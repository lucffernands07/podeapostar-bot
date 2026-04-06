import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES --- #
BSD_TOKEN = os.getenv('BSD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://sports.bzzoiro.com/api"

def get_stats_e_historico(team_name):
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
                # Aqui está o segredo: buscar o detalhe do evento finalizado
                res_detalhe = requests.get(f"{BASE_URL}/events/{j['id']}/", headers=headers)
                if res_detalhe.status_code == 200:
                    detalhes = res_detalhe.json()
                    
                    # Tentamos pegar de 'live_stats' OU 'stats' OU 'statistics'
                    stats_data = detalhes.get("live_stats") or detalhes.get("stats") or detalhes.get("statistics")
                    
                    if stats_data:
                        lado = "home" if detalhes.get('home_team') == team_name else "away"
                        # Busca o campo de chutes a gol (pode variar o nome na API)
                        chutes = stats_data.get(lado, {}).get("shots_on_target") or \
                                 stats_data.get(lado, {}).get("on_target_scoring_attempt", 0)
                        
                        chutes_totais += int(chutes)
                        jogos_contados += 1
    except Exception as e:
        print(f"Erro ao processar {team_name}: {e}")

    # Se falhar em tudo, a média será 4.5 (total 9.0), mas agora ele vai tentar de verdade
    media_chutes = (chutes_totais / jogos_contados) if jogos_contados > 0 else 4.5
    return historico, media_chutes

def analisar_partida(evento):
    home, away = evento['home_team'], evento['away_team']
    hist_h, med_h = get_stats_e_historico(home)
    hist_a, med_a = get_stats_e_historico(away)
    
    if not hist_h or not hist_a: return None

    # Cálculo Gols 1.5 (Regra 5/5, 4/5)
    def count_gols(jogos):
        return sum(1 for j in jogos if (j.get('home_score') or 0) + (j.get('away_score') or 0) > 1.5)

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
            h_s, a_s = j.get('home_score') or 0, j.get('away_score') or 0
            if (sou_h and h_s < a_s) or (not sou_h and a_s < h_s): derrotas += 1
        ult = jogos[0]
        sou_h_u = ult.get('home_team') == team_name
        h_u, a_u = ult.get('home_score') or 0, ult.get('away_score') or 0
        vit_u = (sou_h_u and h_u > a_u) or (not sou_h_u and a_u > h_u)
        return derrotas, vit_u

    d_h, v_h = get_vitoria_stats(hist_h, home)
    d_a, _ = get_vitoria_stats(hist_a, away)
    
    mercado = ""
    if d_h <= 1 and v_h and d_a >= 2:
        mercado = f"1X (Chance {80 if d_h == 0 else 65}%)"
    elif d_a == 0 and d_h >= 2:
        mercado = f"2X (Chance 90%)"

    return {
        "home": home, "away": away,
        "chance_15": chance_15,
        "vitoria": mercado,
        "escanteio": f"-{med_h + med_a:.1f}"
    }

def realizar_analise():
    hoje = datetime.now().strftime('%Y-%m-%d')
    print(f"🚀 Iniciando análise profunda para {hoje}...")
    
    res = requests.get(f"{BASE_URL}/events/", 
                       headers={"Authorization": f"Token {BSD_TOKEN}"}, 
                       params={"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"})
    
    if res.status_code == 200:
        jogos = res.json().get("results", [])
        aprovados = []
        for j in jogos[:15]:
            analise = analisar_partida(j)
            if analise: 
                aprovados.append(analise)
                print(f"📊 {analise['home']} x {analise['away']} | Chutes somados: {analise['escanteio']}")

        if aprovados:
            bilhete = "🎯 **BILHETE ESTRATÉGICO H2H**\n\n"
            for i, a in enumerate(aprovados, 1):
                bilhete += f"{i}. 🏟️ **{a['home']} x {a['away']}**\n"
                if a['chance_15'] > 0: bilhete += f"🔶 Gols +1.5 (Chance {a['chance_15']}%)\n"
                if a['vitoria']: bilhete += f"💎 Mercado: {a['vitoria']}\n"
                bilhete += f"🚩 Dica: Escanteio {a['escanteio']}\n"
                bilhete += "---\n\n"
            
            enviar_telegram(bilhete)

if __name__ == "__main__":
    realizar_analise()
