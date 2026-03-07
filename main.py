import requests
import json

# --- CONFIGURAÇÃO DE TESTE --- #
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
EVENT_ID = "706859"  # ID do jogo de hoje: Athletic Club x Barcelona
BARCA_ID = "83"

def teste_individual_barca():
    print(f"🚀 INICIANDO TESTE DE FORÇA BRUTA - BARCELONA")
    print("-" * 50)

    # CAMINHO 1: API de Confronto Direto (Head-to-Head)
    # Essa é a mais estável para ver quem "atropela" quem
    url_h2h = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={EVENT_ID}"
    
    try:
        res = requests.get(url_h2h, headers=HEADERS, timeout=10).json()
        
        # Tentativa A: Buscar no 'lastGames' (onde costuma ficar o histórico)
        last_games = res.get('lastGames', [])
        found = False

        for team_data in last_games:
            t_id = str(team_data.get('teamId'))
            if t_id == BARCA_ID:
                print(f"✅ Histórico do Barcelona encontrado no 'lastGames'!")
                eventos = team_data.get('events', [])
                gols_marcados = 0
                over25 = 0
                
                for i, ev in enumerate(eventos[-5:], 1):
                    # Extraindo placar do histórico
                    competitors = ev.get('competitions', [{}])[0].get('competitors', [])
                    t_alvo = next(t for t in competitors if str(t['id']) == BARCA_ID)
                    t_rival = next(t for t in competitors if str(t['id']) != BARCA_ID)
                    
                    gm = int(t_alvo.get('score', 0))
                    gr = int(t_rival.get('score', 0))
                    print(f"   ⚽ Jogo {i}: Barcelona {gm} x {gr} {t_rival['team']['displayName']}")
                    
                    gols_marcados += gm
                    if (gm + gr) >= 3: over25 += 1
                
                print(f"\n📊 RESUMO PARA O ROBÔ:")
                print(f"   - Gols totais (5 jogos): {gols_marcados}")
                print(f"   - Frequência +2.5: {over25}/5")
                found = True
                break

        if not found:
            print("⚠️ 'lastGames' vazio. Tentando CAMINHO 2: Estatísticas da Temporada...")
            # CAMINHO 2: Se o histórico de 5 jogos sumiu, pegamos a média da liga
            # Procuramos dentro de 'seasons' ou 'standings' no JSON do jogo
            standings = res.get('standings', {}).get('groups', [])
            if standings:
                for group in standings:
                    for entry in group.get('standings', {}).get('entries', []):
                        if str(entry.get('team', {}).get('id')) == BARCA_ID:
                            stats = entry.get('stats', [])
                            gp = next((s['displayValue'] for s in stats if s['name'] == 'pointsFor'), "0")
                            j = next((s['displayValue'] for s in stats if s['name'] == 'gamesPlayed'), "1")
                            print(f"✅ Estatísticas da Liga encontradas!")
                            print(f"   - Gols Marcados na Temporada: {gp}")
                            print(f"   - Jogos Disputados: {j}")
                            media = float(gp) / int(j)
                            print(f"   - Média de Gols: {media:.2f} por jogo")
                            found = True

        if not found:
            print("❌ Erro: A ESPN removeu todas as referências de histórico deste JSON.")
            print("DICA: Se isso acontecer, o robô precisa varrer o 'scoreboard' de dias anteriores.")

    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    teste_individual_barca()
                            
