import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Sua configuração original mantida exatamente como você usa
def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

if __name__ == "__main__":
    LISTA_JOGOS = [
        "https://www.flashscore.com.br/jogo/futebol/novorizontino-4lOgZPQl/ponte-preta-WlHjRvDk/h2h/total/",
        "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/iraque-K8aAGt6r/h2h/total/"
    ]
    
    driver = configurar_driver()
    wait = WebDriverWait(driver, 20)

    try:
        for i, url_h2h in enumerate(LISTA_JOGOS):
            print(f"\n🚀 --- TESTANDO JOGO {i+1} ---")
            driver.get(url_h2h)
            
            # Verificação de carregamento
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            except:
                print(f"⚠️ Erro ao carregar H2H. Screenshot salvo em 'erro_{i}.png'")
                driver.save_screenshot(f"erro_{i}.png")
                continue

            # Localiza e clica no primeiro jogo da lista
            linhas = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
            driver.execute_script("arguments[0].click();", linhas[0])
            
            # Navega para a aba de finalizações
            wait.until(lambda d: "/resumo" in d.current_url)
            base_url = driver.current_url.split("/resumo")[0]
            url_fin = f"{base_url}/resumo/estatisticas-jogadores/finalizacoes/"
            driver.get(url_fin)
            
            # Validação básica de coleta
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".wcl-table__row_")))
            jogadores = driver.find_elements(By.CSS_SELECTOR, ".wcl-table__row_")
            print(f"✅ Sucesso! Jogo {i+1} carregado. Identificados {len(jogadores)} registros.")

    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")
