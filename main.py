import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BARCA_ID = "83"

def teste_vapt_vupt():
    print(f"⚡ INICIANDO BUSCA RÁPIDA - BARCELONA (ID: {BARCA_ID})")
    
    # URL de tendência: Traz os últimos jogos de uma vez só
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/soccer/esp.1/teams/{BARCA_ID}/statistics"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        
        # Procura a seção de eventos recentes no JSON
        # A ESPN organiza isso em 'categories' ou 'records'
        print("✅ Conexão estabelecida. Analisando dados...")
        
        # Se não encontrar no 'statistics', vamos no 'team-summary' que é leve
        url_backup = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/teams/{BARCA_ID}"
        res_b = requests.get(url_backup, headers=HEADERS, timeout=10).json()
        
        team_info = res_b.get('team', {})
        print(f"\n🏟️ TIME: {team_info.get('displayName')}")
        
        # Verifica se há link de estatísticas ativo
        if 'links' in team_info:
            print("🔗 Links de dados ativos: OK")
        
        # Puxa o histórico de forma simplificada
        record = team_info.get('record', {}).get('items', [{}])[0].get('stats', [])
        for s in record:
            if s['name'] in ['pointsFor', 'goalsFor', 'gamesPlayed']:
                print(f"   📊 {s['description']}: {s['displayValue']}")

        print("\n🚀 Se os dados acima apareceram, a API está respondendo!")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    teste_vapt_vupt()
    
