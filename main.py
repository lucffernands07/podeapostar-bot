import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
BSD_TOKEN = os.getenv('BSD_TOKEN')
BASE_URL = "https://sports.bzzoiro.com/api"

def get_historico(team_name=None, league_id=None):
    """Busca histórico filtrando pela liga para garantir o time correto (Ex: Arsenal da elite)."""
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    
    # 1. Tenta buscar o histórico do time DENTRO da mesma liga/copa do jogo de hoje
    # Isso evita misturar Arsenal (Champions) com Arsenal (Sub-20 ou outras ligas)
    params = {
        "team": team_name,
        "league_id": league_id,
        "date_to": ontem,
        "status": "finished",
        "tz": "America/Sao_Paulo"
    }

    try:
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        if res.status_code == 200:
            resultados = res.json().get("results", [])
            
            # Se encontrar pelo menos 5 jogos na liga específica (Premier, Champions, etc)
            if len(resultados) >= 5:
                placares = [f"{j.get('home_score')}x{j.get('away_score')}" for j in resultados[:5]]
                print(f"🏟️ Histórico de Elite para {team_name} (Liga {league_id}): {placares}")
                return resultados[:5]
            
            # 2. Se não achou 5 jogos na liga (ex: time em copa), busca o histórico geral pelo nome
            params.pop("league_id")
            res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
            if res.status_code == 200:
                resultados = res.json().get("results", [])
                if len(resultados) >= 5:
                    return resultados[:5]
    except:
        return []
    return []

def calcular_chance_gols(hist_h, hist_a, limite):
    def count_gols(jogos):
        return sum(1 for j in jogos if (j.get('home_score') or 0) + (j.get('away_score') or 0) > limite)
    
    g_h, g_a = count_gols(hist_h), count_gols(hist_a)
    # Sua regra exata de 4/5 e 5/5
    if g_h == 5 and g_a == 5: return 100
    elif (g_h == 5 and g_a == 4) or (g_h == 4 and g_a == 5): return 85
    elif g_h == 4 and g_a == 4: return 70
    return 0

def analisar_partida(evento):
    home_name = evento.get('home_team')
    away_name = evento.get('away_team')
    league_id = evento.get('league_id') # Identifica se é Champions, Serie A, etc.

    # Busca histórico com filtro de liga para evitar "Arsenais" errados
    hist_h = get_historico(team_name=home_name, league_id=league_id)
    hist_a = get_historico(team_name=away_name, league_id=league_id)
    
    # Regra de segurança: precisa de 5 jogos para análise
    if len(hist_h) < 5 or len(hist_a) < 5: 
        return None

    chance_15 = calcular_chance_gols(hist_h, hist_a, 1.5)
    chance_25 = calcular_chance_gols(hist_h, hist_a, 2.5)

    def get_vitoria_stats(jogos, team_n):
        derrotas = 0
        for j in jogos:
            sou_h = j.get('home_team') == team_n
            h_s, a_s = j.get('home_score') or 0, j.get('away_score') or 0
            if (sou_h and h_s < a_s) or (not sou_h and a_s < h_s): derrotas += 1
        
        if not jogos: return 5, False
        ult = jogos[0]
        sou_h_u = ult.get('home_team') == team_n
        h_u, a_u = ult.get('home_score') or 0, ult.get('away_score') or 0
        vit_u = (sou_h_u and h_u > a_u) or (not sou_h_u and a_u > h_u)
        return derrotas, vit_u

    d_h, v_h = get_vitoria_stats(hist_h, home_name)
    d_a, _ = get_vitoria_stats(hist_a, away_name)
    
    mercado = ""
    if d_h <= 1 and v_h and d_a >= 2: 
        mercado = f"1X (Chance {80 if d_h == 0 else 65}%)"
    elif d_a == 0 and d_h >= 2: 
        mercado = f"2X (Chance 90%)"

    return {
        "home": home_name, 
        "away": away_name,
        "chance_15": chance_15,
        "chance_25": chance_25,
        "vitoria": mercado
    }

def realizar_analise():
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"}

    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    if res.status_code == 200:
        todos_jogos = res.json().get("results", [])
        print(f"📡 Analisando {len(todos_jogos)} jogos do dia...")
        
        for j in todos_jogos:
            # Pula jogos que já aconteceram
            if j.get('status') == 'finished': continue
            
            a = analisar_partida(j)
            # Imprime no log para você acompanhar
            if a:
                print(f"🏟️ {a['home']} x {a['away']} | +1.5: {a['chance_15']}% | +2.5: {a['chance_25']}%")

if __name__ == "__main__":
    realizar_analise()
