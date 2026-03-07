import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
BARCA_ID = "83"

def teste_final_barca():
    print(f"🚀 TESTE FINAL - EXTRAÇÃO DE GOLS")
    # Usando a URL de estatísticas da liga para o time
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/teams/{BARCA_ID}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        stats = res.get('team', {}).get('record', {}).get('items', [{}])[0].get('stats', [])
        
        if not stats:
            print("❌ Não encontrei a lista de stats. Tentando caminho alternativo...")
            return

        print(f"\n✅ DADOS DO BARCELONA:")
        for s in stats:
            # Procuramos pelos códigos internos: 'pointsFor' (Gols Marcados) e 'gamesPlayed' (Jogos)
            if s.get('name') == 'pointsFor':
                print(f"   ⚽ Gols Marcados na Temporada: {s.get('displayValue')}")
            if s.get('name') == 'gamesPlayed':
                print(f"   📅 Total de Jogos na Liga: {s.get('displayValue')}")
                
        print("\n🚀 Se os números de Gols e Jogos apareceram, o erro acabou!")

    except Exception as e:
        print(f"❌ Erro ao processar: {e}")

if __name__ == "__main__":
    teste_final_barca()
    
