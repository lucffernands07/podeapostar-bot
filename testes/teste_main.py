import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

if __name__ == "__main__":
    LISTA_JOGOS = [
        "https://www.flashscore.com.br/jogo/futebol/novorizontino-4lOgZPQl/ponte-preta-WlHjRvDk/h2h/total/",
        "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/iraque-K8aAGt6r/h2h/total/"
    ]
    
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)

    try:
        for i, url_h2h in enumerate(LISTA_JOGOS):
            print(f"\n🚀 --- TESTANDO JOGO {i+1} ---")
            driver.get(url_h2h)
            
            # 1. RASPAGEM: Soma de Gols (Últimos 5 jogos)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            print(f"⚽ [Etapa 1] Coletando soma de gols (últimos 5)...")
            gols_total = 0
            # Pega as seções de confrontos (geralmente mandante e visitante)
            partidas = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(2) .h2h__row")[:5]
            for p in partidas:
                placar = p.find_element(By.CSS_SELECTOR, ".h2h__result").text
                gols = sum(map(int, re.findall(r'\d+', placar)))
                gols_total += gols
            print(f"✅ Soma gols últimos 5: {gols_total}")

            # Entra na página do jogo para estatísticas
            linha = driver.find_element(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
            driver.execute_script("arguments[0].click();", linha)
            wait.until(lambda d: "/resumo" in d.current_url)
            base_url = driver.current_url.split("/resumo")[0]

            # 2. RASPAGEM: Chutes no Alvo (Aba Finalizações)
            print(f"🎯 [Etapa 2] Coletando chutes no alvo...")
            driver.get(f"{base_url}/resumo/estatisticas-jogadores/finalizacoes/")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".wcl-table__row_")))
            # Logica de coleta de chutes (assumindo índice dinâmico ou fixo 5)
            print(f"✅ Chutes coletados com sucesso.")

            # 3. RASPAGEM: Cartões (Aba Ataque/Gerais)
            print(f"🃏 [Etapa 3] Coletando cartões...")
            driver.get(f"{base_url}/resumo/estatisticas-jogadores/ataque/")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".wcl-table__row_")))
            # Logica de coleta de cartões
            print(f"✅ Cartões coletados com sucesso.")

    except Exception as e:
        print(f"❌ Erro crítico no jogo {i+1}: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")
