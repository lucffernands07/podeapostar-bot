import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
BARCA_ID = "83"

def auditoria_estatistica_barca():
    print(f"🔎 ACESSANDO ABA DE ESTATÍSTICAS REAIS: BARCELONA (ID: {BARCA_ID})")
    
    # URL que foca nas estatísticas da Liga (LaLiga)
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/statistics?team={BARCA_ID}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        
        # Procura a categoria de "Gols" (Scoring)
        stats = res.get('stats', [])
        
        if not stats:
            print("❌ Não foi possível carregar as estatísticas de gols.")
            # Tentativa alternativa via API de Summary de Liga
            return

        print("\n✅ DADOS ENCONTRADOS NO SISTEMA:")
        
        for category in stats:
            if category.get('name') == 'scoring':
                for stat in category.get('stats', []):
                    nome = stat.get('displayName')
                    valor = stat.get('displayValue')
                    print(f"   📊 {nome}: {valor}")

        print("\n🚀 Se os números acima apareceram (Gols, Assistências),")
        print("   o robô principal vai usar a média de gols para decidir!")

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    auditoria_estatistica_barca()
    
