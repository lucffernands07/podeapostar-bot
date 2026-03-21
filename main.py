import requests
import time
import os

# --- CONFIGURAÇÃO ---
API_KEY = os.getenv('X_RAPIDAPI_KEY') # Certifique-se de que sua chave está no ambiente
HEADERS = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': API_KEY
}

# IDs da API Football (Everton: 45 | Chelsea: 49)
TEAMS = {
    "Everton": 45,
    "Chelsea": 49
}

def testar_media_chutes(team_name, team_id):
    print(f"\n📊 Analisando os últimos 10 jogos de: {team_name} (ID: {team_id})")
    print("-" * 50)
    
    # Busca as últimas 10 partidas finalizadas (FT) do time
    url_fixtures = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
    
    try:
        res = requests.get(url_fixtures, headers=HEADERS).json()
        fixtures = res.get('response', [])
        
        if not fixtures:
            print(f"❌ Nenhum jogo encontrado para {team_name}.")
            return 0

        total_shots = 0
        jogos_processados = 0

        for f in fixtures:
            f_id = f['fixture']['id']
            data = f['fixture']['date'][:10]
            oponente = f['teams']['away']['name'] if f['teams']['home']['id'] == team_id else f['teams']['home']['name']
            
            # Busca as estatísticas específicas desse jogo
            url_stats = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_stats = requests.get(url_stats, headers=HEADERS).json()
            
            stats_data = res_stats.get('response', [])
            shots_neste_jogo = 0
            
            if stats_data:
                for s in stats_data[0].get('statistics', []):
                    if s['type'] == 'Total Shots':
                        shots_neste_jogo = int(s['value']) if s['value'] else 0
                        break
            
            total_shots += shots_neste_jogo
            jogos_processados += 1
            
            print(f"📅 {data} | vs {oponente.ljust(15)} | Chutes: {shots_neste_jogo}")
            
            # Pequeno delay para evitar bloqueio da API (Rate Limit)
            time.sleep(0.5)

        media = total_shots / jogos_processados if jogos_processados > 0 else 0
        print("-" * 50)
        print(f"✅ MÉDIA FINAL {team_name}: {media:.2f} chutes/jogo")
        return media

    except Exception as e:
        print(f"⚠️ Erro ao processar {team_name}: {e}")
        return 0

def rodar_teste_completo():
    # 1. Coleta dados do Everton
    media_everton = testar_media_chutes("Everton", TEAMS["Everton"])
    
    # 2. Coleta dados do Chelsea
    media_chelsea = testar_media_chutes("Chelsea", TEAMS["Chelsea"])
    
    # 3. Cálculo Final (O que vai para o bilhete)
    media_combinada = (media_everton + media_chelsea) / 2
    
    print("\n" + "="*50)
    print(f"🎯 RESULTADO PARA O BILHETE (Everton x Chelsea)")
    print(f"📈 Média Combinada de Chutes: {media_combinada:.2f}")
    
    if media_combinada <= 10.5:
        print(f"💡 Dica sugerida: ESCANTEIO MENOS DE ({media_combinada:.1f})")
    else:
        print(f"⏭️ Jogo descartado para Escanteios (Média muito alta: {media_combinada:.2f})")
    print("="*50)

if __name__ == "__main__":
    rodar_teste_completo()
    
