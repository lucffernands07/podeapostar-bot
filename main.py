import requests
import json

def testar_conexao_real():
    team_id = "186" # ID do Real Madrid
    print(f"--- INICIANDO TESTE PARA O TIME ID: {team_id} (Real Madrid) ---")
    
    # Tentando a URL que o robô usa
    url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status da Resposta: {response.status_code}")
        
        data = response.json()
        # Pega os últimos 5 jogos finalizados
        eventos = [e for e in data.get('events', []) if e.get('status', {}).get('type', {}).get('state') == 'post'][-5:]
        
        print(f"Jogos finalizados encontrados: {len(eventos)}")
        print("-" * 30)

        for i, ev in enumerate(eventos, 1):
            nome_jogo = ev.get('name', 'Sem nome')
            data_jogo = ev.get('date', 'Sem data')
            comp = ev['competitions'][0]['competitors']
            
            # Tenta extrair os gols
            gols_casa = comp[0].get('score', 'N/A')
            gols_fora = comp[1].get('score', 'N/A')
            time_casa = comp[0]['team']['displayName']
            time_fora = comp[1]['team']['displayName']

            print(f"Jogo {i}: {nome_jogo}")
            print(f"Data: {data_jogo}")
            print(f"Placar: {time_casa} {gols_casa} x {gols_fora} {time_fora}")
            
            # Teste de Ambas Marcam
            try:
                g1 = int(gols_casa)
                g2 = int(gols_fora)
                print(f"Análise: {'✅ AMBAS MARCAM' if g1 > 0 and g2 > 0 else '❌ SÓ UM MARCOU'}")
                print(f"Total Gols: {g1 + g2} ({'✅ +1.5' if (g1+g2) >= 2 else '❌ -1.5'})")
            except:
                print("Análise: Erro ao converter gols para número (API mandou dado vazio)")
            print("-" * 30)

    except Exception as e:
        print(f"ERRO CRÍTICO NA CONEXÃO: {e}")

if __name__ == "__main__":
    testar_conexao_real()
                
