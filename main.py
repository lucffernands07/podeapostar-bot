import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def testar_odds_real():
    driver = configurar_driver()
    # URL DIRETA DA ABA ACIMA/ABAIXO
    url = "https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-W8mj7MDD/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    
    try:
        print(f"🚀 Iniciando teste: Bétis x Real Madrid", flush=True)
        driver.get(url)
        
        # Espera o carregamento da tabela
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        
        print("🔍 Buscando odds de +1.5 Gols...", flush=True)
        time.sleep(3) # Tempo extra para o JS das odds preencher os valores
        
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        encontrou = False
        for linha in linhas:
            # Verifica se a linha é de 1.5 gols
            if "1.5" in linha.text:
                valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                if len(valores) >= 2:
                    print(f"✅ SUCESSO! ACIMA 1.5: {valores[0].text}", flush=True)
                    encontrou = True
                    break
        
        if not encontrou:
            print("❌ Linha '1.5' não encontrada.", flush=True)

    except Exception as e:
        print(f"⚠️ Erro: {str(e)[:100]}", flush=True)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_odds_real()
