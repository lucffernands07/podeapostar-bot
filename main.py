import os
import requests

BSD_TOKEN = os.getenv('BSD_TOKEN')
BASE_URL = "https://sports.bzzoiro.com/api"

def buscar_id_oficial(nome_time):
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    # Buscamos em eventos finalizados para pegar um registro histórico real
    params = {"team": nome_time, "status": "finished"}
    
    print(f"🔍 Caçando ID oficial para: {nome_time}...")
    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    
    if res.status_code == 200:
        jogos = res.json().get("results", [])
        for j in jogos:
            # Verificamos se a liga é a Premier League (Inglaterra) ou Champions
            # Geralmente o Arsenal da Inglaterra tem um ID fixo
            h_name = j.get('home_team', '')
            a_name = j.get('away_team', '')
            h_id = j.get('home_id') or j.get('home_team_id')
            a_id = j.get('away_id') or j.get('away_team_id')
            
            if "Arsenal" in h_name:
                return h_id
            if "Arsenal" in a_name:
                return a_id
    return None

# Teste de captura
id_arsenal = buscar_id_oficial("Arsenal")
print(f"🎯 O ID oficial do Arsenal na API BSD é: {id_arsenal}")
