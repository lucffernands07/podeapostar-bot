import os, requests, json

API_KEY = os.getenv('X_RAPIDAPI_KEY')
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def diagnostico():
    # IDs de exemplo (Lazio x Sassuolo e Espanyol x Oviedo - IDs comuns para hoje)
    # Vou buscar as predições de um jogo da Serie A de hoje para teste
    url_fixtures = "https://api-football-v1.p.rapidapi.com/v3/fixtures?date=2026-03-09&league=135&season=2025"
    res = requests.get(url_fixtures, headers=HEADERS).json()
    
    if res.get('response'):
        f_id = res['response'][0]['fixture']['id']
        t1 = res['response'][0]['teams']['home']['name']
        t2 = res['response'][0]['teams']['away']['name']
        
        print(f"🔍 TESTANDO JOGO: {t1} x {t2} (ID: {f_id})")
        
        url_pred = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={f_id}"
        pred_res = requests.get(url_pred, headers=HEADERS).json()
        
        # IMPRIME O BLOCO DE PREDIÇÃO INTEIRO PARA VOCÊ VER
        print("--- DADOS BRUTOS DA API ---")
        print(json.dumps(pred_res['response'][0]['predictions'], indent=2))
        print("--- CONSELHO (ADVICE) ---")
        print(pred_res['response'][0]['predictions'].get('advice'))
    else:
        print("❌ Nenhum jogo encontrado na Serie A para o teste.")

if __name__ == "__main__":
    diagnostico()
    
