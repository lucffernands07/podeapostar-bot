import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO RAPIDAPI (Certifique-se que as variáveis de ambiente estão no GitHub) ---
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': API_KEY
}

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def obter_media_chutes_rapidapi(team_id, nome_log):
    """ Busca a média de 'Total Shots' nos últimos 10 jogos via RapidAPI """
    try:
        print(f"[API] Buscando últimos 10 jogos do {nome_log} (ID: {team_id})...")
        # 1. Busca os últimos 10 jogos finalizados
        url_fixtures = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10&status=FT"
        res = requests.get(url_fixtures, headers=HEADERS).json()
        fixtures = res.get('response', [])
        
        if not fixtures:
            print(f"⚠️ Nenhum jogo encontrado para {nome_log}")
            return 0

        total_shots = 0
        contagem_jogos = 0

        for f in fixtures:
            f_id = f['fixture']['id']
            # 2. Busca estatísticas detalhadas do jogo
            url_stats = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={f_id}&team={team_id}"
            res_s = requests.get(url_stats, headers=HEADERS).json()
            
            stats_data = res_s.get('response', [])
            if stats_data:
                # Procura o item 'Total Shots'
                stats_list = stats_data[0].get('statistics', [])
                for s in stats_list:
                    if s['type'] == 'Total Shots':
                        valor = s['value'] or 0
                        total_shots += valor
                        contagem_jogos += 1
                        print(f"   -> Jogo {f_id}: {valor} chutes")
                        break
            
            time.sleep(0.5) # Evita bloqueio por excesso de requisições (Rate Limit)

        media = total_shots / contagem_jogos if contagem_jogos > 0 else 0
        print(f"✅ [MÉDIA {nome_log}]: {media:.2f} chutes")
        return media

    except Exception as e:
        print(f"❌ Erro na RapidAPI para {nome_log}: {e}")
        return 0

def executar_teste_rapidapi():
    # Times de teste (Você pode mudar para os IDs da RapidAPI se já souber)
    t1_nome = "Bahia"
    t1_id_rapid = 118 # ID Exemplo Bahia na RapidAPI
    t2_nome = "Bragantino"
    t2_id_rapid = 1128 # ID Exemplo Bragantino na RapidAPI

    print(f"\n🚀 === INICIANDO TESTE DE FINALIZAÇÕES (RAPIDAPI) === 🚀")
    
    # [PASSO 1] CÁLCULO DAS MÉDIAS
    media_casa = obter_media_chutes_rapidapi(t1_id_rapid, t1_nome)
    media_fora = obter_media_chutes_rapidapi(t2_id_rapid, t2_nome)

    # [PASSO 2] CÁLCULO FINAL E REGRA DE PORCENTAGEM
    print(f"\n📊 === RESULTADO FINAL === 📊")
    if media_casa > 0 and media_fora > 0:
        media_final = (media_casa + media_fora) / 2
        
        # Sua regra de confiança
        confianca = "0%"
        if media_final <= 5.0: confianca = "100%"
        elif media_final <= 7.0: confianca = "90%"
        elif media_final <= 10.5: confianca = "80%"

        print(f"🎯 Média Combinada: {media_final:.2f} chutes")
        
        if media_final <= 10.5:
            print(f"✅ ENTRADA APROVADA: {confianca} de confiança")
        else:
            print(f"⚠️ REJEITADO: Média {media_final:.2f} > 10.5")
    else:
        print("❌ Falha ao obter dados suficientes da RapidAPI.")

if __name__ == "__main__":
    executar_teste_rapidapi()
