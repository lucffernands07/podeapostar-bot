import requests
import time
import os

# --- CONFIGURAÇÃO ---
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': API_KEY
}

# IDs OFICIAIS DA API (Aston Villa: 66 | West Ham: 48)
TEAMS = {
    "Aston Villa": 66,
    "West Ham": 48
}

def testar_media_chutes(team_name, team_id):
    print(f"\n📊 Analisando os últimos 10 jogos de: {team_name} (ID: {team_id})")
    print("-" * 60)
    
    # Busca as últimas 10 partidas FINALIZADAS antes de hoje
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
            
            # Identifica o oponente
            home_team = f['teams']['home']['name']
            away_team = f['teams']['away']['name']
            oponente = away_team if f['teams']['home']['id'] == team_id else home_team
            
            # Busca as estatísticas específicas desse jogo para o time
            url_stats = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_stats = requests.get(url_stats, headers=HEADERS).json()
            
            stats_data = res_stats.get('response', [])
            shots_neste_jogo = 0
            
            if stats_data:
                # Procura o campo 'Total Shots' dentro da lista de estatísticas
                for s in stats_data[0].get('statistics', []):
                    if s['type'] == 'Total Shots':
                        # Se o valor for None (vazio na API), tratamos como 0
                        shots_neste_jogo = int(s['value']) if s['value'] is not None else 0
                        break
            
            total_shots += shots_neste_jogo
            jogos_processados += 1
            
            print(f"📅 {data} | vs {oponente.ljust(18)} | Chutes Totais: {shots_neste_jogo}")
            
            # Delay para respeitar o limite da API (Free Tier)
            time.sleep(0.6)

        media = total_shots / jogos_processados if jogos_processados > 0 else 0
        print("-" * 60)
        print(f"✅ MÉDIA FINAL {team_name}: {media:.2f} chutes/jogo")
        return media

    except Exception as e:
        print(f"⚠️ Erro ao processar {team_name}: {e}")
        return 0

def rodar_validacao():
    print("🚀 INICIANDO VALIDAÇÃO DE LOGS (ASTON VILLA x WEST HAM)")
    
    media_villa = testar_media_chutes("Aston Villa", TEAMS["Aston Villa"])
    media_wh = testar_media_chutes("West Ham", TEAMS["West Ham"])
    
    media_combinada = (media_villa + media_wh) / 2
    
    print("\n" + "="*60)
    print(f"🎯 RESULTADO FINAL DO CÁLCULO")
    print(f"📈 Média Villa: {media_villa:.2f}")
    print(f"📈 Média West Ham: {media_wh:.2f}")
    print(f"🔥 MÉDIA COMBINADA (O que foi pro Telegram): {media_combinada:.2f}")
    print("="*60)
    
    if media_combinada < 6:
        print("💡 CONCLUSÃO: A média deu muito baixa (5.2) porque a API")
        print("registrou poucos 'Total Shots' nos jogos anteriores destes times.")
    else:
        print("💡 CONCLUSÃO: Os dados estão consistentes com a média.")

if __name__ == "__main__":
    rodar_validacao()
            
