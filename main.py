import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def obter_media_chutes_api(id_time, nome_log):
    """Consulta a API para pegar a média de chutes dos últimos 10 jogos"""
    try:
        print(f"[API] Calculando média dos últimos 10 jogos para: {nome_log}...")
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # 1. Pega os últimos eventos do time
        url_eventos = f"https://api.sofascore.com/api/v1/team/{id_time}/events/last/0"
        res = requests.get(url_eventos, headers=headers)
        eventos = res.json().get('events', [])[:10]
        
        total_chutes = 0
        contagem = 0

        for evento in eventos:
            id_jogo = evento.get('id')
            # 2. Pega estatística detalhada de cada jogo
            url_stats = f"https://api.sofascore.com/api/v1/event/{id_jogo}/statistics"
            res_s = requests.get(url_stats, headers=headers)
            stats_data = res_s.json()
            
            # Navega no JSON para achar 'Total de finalizações'
            for periodo in stats_data.get('statistics', []):
                if periodo.get('period') == 'ALL': # Estatística do jogo todo
                    for grupo in periodo.get('groups', []):
                        if grupo.get('groupName') == 'Atacando':
                            for item in grupo.get('statisticsItems', []):
                                if item.get('name') == 'Total de finalizações':
                                    # Verifica se o time era Home ou Away no jogo passado
                                    is_home = evento['homeTeam']['id'] == int(id_time)
                                    valor = item['homeValue'] if is_home else item['awayValue']
                                    total_chutes += int(valor)
                                    contagem += 1
        
        media = total_chutes / contagem if contagem > 0 else 0
        print(f"✅ [API] {nome_log}: {media:.2f} chutes (Base: {contagem} jogos)")
        return media
    except Exception as e:
        print(f"❌ Erro API {nome_log}: {e}")
        return 0

def executar_bot_hibrido():
    t1_name = "Bahia"
    t2_name = "Red Bull Bragantino"
    
    print(f"\n🚀 === INICIANDO PROCESSO (SELENIUM + API) === 🚀")
    driver = configurar_browser()
    wait = WebDriverWait(driver, 25)
    
    try:
        # [PASSO 1] BUSCA DO CONFRONTO
        print(f"[LOG 1] Buscando link do confronto no SofaScore...")
        driver.get("https://www.sofascore.com/pt/")
        
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(8)
        
        resultado = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/football/match/')]")))
        url_confronto = resultado.get_attribute("href")
        print(f"✅ Confronto Encontrado: {url_confronto}")
        
        driver.get(url_confronto)
        time.sleep(5)

        # [PASSO 2] CAPTURA DE IDs DOS TIMES VIA SELENIUM
        print(f"[LOG 2] Extraindo IDs dos times para consulta API...")
        
        def extrair_id(xpath):
            link = driver.find_element(By.XPATH, xpath).get_attribute("href")
            # O ID é o último conjunto de números na URL: .../team/nome/ID
            return link.split('/')[-1]

        id_casa = extrair_id(f"//a[contains(., '{t1_name}')]")
        id_fora = extrair_id(f"//a[contains(., '{t2_name}')]")
        
        print(f"🆔 ID {t1_name}: {id_casa} | ID {t2_name}: {id_fora}")

        # [PASSO 3] CONSULTA API (10 JOGOS)
        media_casa = obter_media_chutes_api(id_casa, t1_name)
        media_fora = obter_media_chutes_api(id_fora, t2_name)

        # [PASSO 4] CÁLCULO E REGRA DE PORCENTAGEM
        print(f"\n📊 === RESULTADO FINAL === 📊")
        if media_casa > 0 and media_fora > 0:
            media_final = (media_casa + media_fora) / 2
            
            # Sua regra de porcentagem
            porcentagem = "0%"
            if media_final <= 5.0:
                porcentagem = "100%"
            elif media_final <= 7.0:
                porcentagem = "90%"
            elif media_final <= 10.5:
                porcentagem = "80%"

            print(f"🎯 Média Combinada: {media_final:.2f} chutes")
            
            if media_final <= 10.5:
                print(f"✅ ENTRADA CONFIRMADA: {porcentagem} de confiança")
            else:
                print(f"⚠️ REJEITADO: Média acima de 10.5 ({media_final:.2f})")
        else:
            print("❌ Falha crítica ao obter dados da API.")

    except Exception as e:
        print(f"❌ Erro no Processo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    executar_bot_hibrido()
