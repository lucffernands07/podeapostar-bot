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
    # User-agent para o site não bloquear o bot
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def testar_odds_real():
    driver = configurar_driver()
    url = "https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-W8mj7MDD/?mid=lfKIYGgU"
    
    try:
        print(f"🚀 Iniciando teste no jogo: Bétis x Real Madrid")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # 1. Clicar na aba 'Odds'
        print("🖱️ Clicando em 'Odds'...")
        btn_odds = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Odds')]")))
        btn_odds.click()
        time.sleep(2)

        # 2. Clicar em 'Acima/Abaixo'
        print("🖱️ Clicando em 'Acima/Abaixo'...")
        btn_over_under = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acima/Abaixo')]")))
        btn_over_under.click()
        time.sleep(3)

        # 3. Captura dos dados
        print("🔍 Buscando odds...")
        # Localiza todas as linhas de gols
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        for linha in linhas:
            if "1.5" in linha.text:
                # Usa o data-testid que você mapeou
                valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                if len(valores) >= 2:
                    print(f"✅ Encontrado! ACIMA 1.5: {valores[0].text} | ABAIXO 1.5: {valores[1].text}")
                    return # Sucesso!
        
        print("❌ Linha '1.5' não encontrada na tabela.")

    except Exception as e:
        print(f"⚠️ Erro no teste: {str(e)[:100]}...") # Printa apenas o começo do erro
        driver.save_screenshot("erro_teste.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_odds_real()
