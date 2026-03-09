import os
import requests
import json

# --- CONFIGURAÇÃO --- #
API_KEY = "a09ce48543msh617f960e6fbcb8dp1b8d01jsned842e01d8f5"
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def testar_jogo_especifico(match_name, league_id, team_home_id, team_away_id, season):
    print(f"🔬 --- RAIO-X DO JOGO: {match_name} ---")
    
    # URL onde a API busca as estatísticas de desempenho da temporada
    url_home = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?league={league_id}&team={team_home_id}&season={season}"
    url_away = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?league={league_id}&team={team_away_id}&season={season}"
    
    try:
        res_h = requests.get(url_home, headers=HEADERS).json()['response']
        res_a = requests.get(url_away, headers=HEADERS).json()['response']

        # DADOS QUE A API ESTÁ VENDO (O que o robô usa para decidir)
        stats = {
            "Home (Casa)": {
                "Gols Marcados": res_h['goals']['for']['total']['total'],
                "Jogos Feitos": res_h['fixtures']['played']['total'],
                "Ambas Marcam (BTTS)": res_h['goals']['both_teams_score']['percentage'],
                "Média Escanteios": res_h['corners']['avg']
            },
            "Away (Fora)": {
                "Gols Marcados": res_a['goals']['for']['total']['total'],
                "Jogos Feitos": res_a['fixtures']['played']['total'],
                "Ambas Marcam (BTTS)": res_a['goals']['both_teams_score']['percentage'],
                "Média Escanteios": res_a['corners']['avg']
            }
        }
        
        # Exibe o JSON que a API entregou (Igual ao "conteúdo da página" do FootyStats)
        print(json.dumps(stats, indent=4, ensure_ascii=False))
        
        # VALIDAÇÃO DO ROBÔ
        media_gols = (stats['Home (Casa)']['Gols Marcados'] / stats['Home (Casa)']['Jogos Feitos'] + 
                      stats['Away (Fora)']['Gols Marcados'] / stats['Away (Fora)']['Jogos Feitos']) / 2
        
        print(f"\n✅ CONCLUSÃO DO ROBÔ PARA {match_name}:")
        print(f"📊 Média Combinada de Gols: {media_gols:.2f}")
        
        if media_gols > 1.8: print("🎯 Mercado sugerido: +1.5 Gols")
        if float(stats['Home (Casa)']['Média Escanteios'] or 0) > 4.5: print("🎯 Mercado sugerido: +8.5 Cantos")

    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")

# TESTE REAL: Lazio (487) x Sassuolo (489) | Liga: Serie A (135) | Temporada: 2025
if __name__ == "__main__":
    testar_jogo_especifico("Lazio x Sassuolo", 135, 487, 489, 2025)
        
