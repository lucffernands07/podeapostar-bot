import os
import requests
import time
import pytz
from datetime import datetime

# --- CONFIGURAÇÃO --- #
API_KEY = os.getenv('API_SPORTS_KEY') 
HEADERS = {'x-apisports-key': API_KEY}
URL_BASE = "https://v3.football.api-sports.io"

def log_teste(etapa, msg):
    print(f"🔍 [TESTE {etapa}] {msg}")

def get_avg_shots_api(team_id, team_name):
    # Pega os últimos 10 jogos finalizados
    url = f"{URL_BASE}/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS).json()
        fixtures = res.get('response', [])
        total_shots = 0
        jogos_com_dados = 0
        
        for f in fixtures:
            f_id = f['fixture']['id']
            # Busca estatística detalhada de cada jogo
            url_s = f"{URL_BASE}/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_s = requests.get(url_s, headers=HEADERS).json()
            stats_list = res_s.get('response', [])
            
            if stats_list and 'statistics' in stats_list[0]:
                for s in stats_list[0]['statistics']:
                    if s['type'] == 'Total Shots' and s['value'] is not None:
                        total_shots += int(s['value'])
                        jogos_com_dados += 1
                        break
            time.sleep(0.5) # Respeita o limite de requisições por minuto do plano Free
            
        media = total_shots / jogos_com_dados if jogos_com_dados > 0 else 0
        log_teste("CHUTES", f"{team_name}: Média de {media:.2f} chutes (em {jogos_com_dados} jogos)")
        return media
    except Exception as e:
        print(f"Erro ao calcular chutes: {e}")
        return 0

def testar_juventus_hoje():
    # Define a data de hoje no fuso de SP
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
    
    log_teste("BUSCA", f"Buscando jogos de hoje ({hoje}) na Serie A (ID: 135)...")
    
    # Busca por DATA e LEAGUE (Permitido no plano Free)
    # Importante: Na API-Sports, a temporada 25/26 é identificada como 2025
    url = f"{URL_BASE}/fixtures?date={hoje}&league=135&season=2025"
    
    try:
        res = requests.get(url, headers=HEADERS).json()
        
        if 'errors' in res and res['errors']:
            print(f"❌ ERRO DA API: {res['errors']}")
            return

        fixtures = res.get('response', [])
        if not fixtures:
            log_teste("AVISO", "Nenhum jogo da Serie A encontrado para hoje nesta temporada.")
            return

        match = None
        for f in fixtures:
            if "Juventus" in f['teams']['home']['name'] or "Juventus" in f['teams']['away']['name']:
                match = f
                break

        if not match:
            log_teste("ERRO", "Jogo da Juventus não encontrado na lista de hoje.")
            # Opcional: imprimir nomes dos times encontrados para conferência
            times_hoje = [f"{f['teams']['home']['name']} x {f['teams']['away']['name']}" for f in fixtures]
            print(f"Jogos encontrados hoje: {times_hoje}")
            return

        t1, t2 = match['teams']['home'], match['teams']['away']
        status = match['fixture']['status']['long']
        print(f"\n🏟️  JOGO LOCALIZADO: {t1['name']} x {t2['name']}")
        print(f"⏰ Horário (UTC): {match['fixture']['date']}")
        print(f"📊 Status Atual: {status}")
        print("-" * 50)

        # Rodar teste de chutes para os dois times
        s1 = get_avg_shots_api(t1['id'], t1['name'])
        s2 = get_avg_shots_api(t2['id'], t2['name'])
        
        print(f"\n✅ RESULTADO FINAL: Média Combinada de {(s1+s2)/2:.2f} chutes.")

    except Exception as e:
        print(f"❌ Erro ao processar: {e}")

if __name__ == "__main__":
    testar_juventus_hoje()
