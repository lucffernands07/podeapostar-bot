import time
import re
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

def buscar_id_pela_pesquisa(termo):
    driver = configurar_browser()
    print(f"\n🚀 --- INICIANDO BUSCA POR MENU: {termo} ---")
    
    try:
        # 1. ACESSA O SITE
        driver.get("https://www.sofascore.com/pt/")
        wait = WebDriverWait(driver, 20)

        # 2. CLICA NO CAMPO DE PESQUISA (Pelo placeholder ou pela classe assistiva)
        print("🔍 LOG: Clicando no menu de pesquisa...")
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()

        # 3. DIGITA O NOME DOS TIMES
        print(f"⌨️ LOG: Digitando '{termo}'...")
        search_input.send_keys(termo)
        time.sleep(5) # Aguarda os resultados aparecerem no dropdown

        # 4. CLICA NO RESULTADO "LAZIO-MILAN"
        # Usamos um XPATH que busca o texto Lazio e Milan no mesmo bloco de resultado
        print("🖱️ LOG: Selecionando o jogo nos resultados...")
        xpath_resultado = "//span[contains(text(), 'Lazio')]/following-sibling::span[contains(text(), '-')]/following-sibling::span[contains(text(), 'Milan')]"
        
        resultado_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(., 'Lazio') and contains(., 'Milan')]/ancestor::a[contains(@href, '/football/match/')]")))
        
        url_final = resultado_link.get_attribute("href")
        resultado_link.click()

        # 5. CAPTURA O ID DA URL
        # A URL segue o padrão: .../match/lazio-milan/ID
        id_jogo = url_final.split("/")[-1]
        
        print(f"\n✅ --- RESULTADO ENCONTRADO ---")
        print(f"🔗 URL DO JOGO: {url_final}")
        print(f"🆔 ID DO JOGO: {id_jogo}")
        
        # 6. VERIFICAÇÃO ADICIONAL (NA PÁGINA DO JOGO)
        wait.until(EC.url_contains(id_jogo))
        print(f"📍 LOG: Navegação confirmada para o ID {id_jogo}")

    except Exception as e:
        print(f"🚨 ERRO DURANTE A BUSCA: {e}")
        driver.save_screenshot("erro_pesquisa.png") # Salva print para debug se der erro
    finally:
        driver.quit()

if __name__ == "__main__":
    # Testando com Lazio e Milan
    buscar_id_pela_pesquisa("lazio milan")
