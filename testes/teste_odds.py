import time
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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def testar_raspagem_direta(url_exata):
    driver = configurar_driver()
    
    # Passo 1: Acesso direto
    print(f"--- PASSO 1: Acessando URL Direta ---")
    print(f"URL: {url_exata}")
    
    try:
        driver.get(url_exata)
        wait = WebDriverWait(driver, 15)
        
        # Espera as linhas da tabela carregarem
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(2) 
        
        print(f"\n--- PASSO 2: Raspagem (Segunda Ocorrência) ---")
        
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        # Dicionário para controlar qual vez o mercado aparece
        contadores = {"1.5": 0, "2.5": 0, "4.5": 0}
        resultados = {}

        for linha in linhas:
            texto_linha = linha.text
            # Busca as células de odd dentro desta linha
            celulas = linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            
            if not celulas:
                continue

            # Verificação para 1.5
            if "1.5" in texto_linha:
                contadores["1.5"] += 1
                if contadores["1.5"] == 2:
                    resultados["GOLS_15"] = celulas[0].text.strip() # Acima (Esquerda)
                    print(f"✅ Segundo 1.5 (Acima) encontrado: {resultados['GOLS_15']}")

            # Verificação para 2.5
            elif "2.5" in texto_linha:
                contadores["2.5"] += 1
                if contadores["2.5"] == 2:
                    resultados["GOLS_25"] = celulas[0].text.strip() # Acima (Esquerda)
                    print(f"✅ Segundo 2.5 (Acima) encontrado: {resultados['GOLS_25']}")

            # Verificação para 4.5
            elif "4.5" in texto_linha:
                contadores["4.5"] += 1
                if contadores["4.5"] == 2:
                    if len(celulas) >= 2:
                        resultados["GOLS_M45"] = celulas[1].text.strip() # Abaixo (Direita)
                        print(f"✅ Segundo 4.5 (Abaixo) encontrado: {resultados['GOLS_M45']}")

        print(f"\n--- RESULTADO FINAL ---")
        print(resultados)

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/botafogo-jXzWoWa5/remo-2i0B6Zul/odds/acima-abaixo/tempo-regulamentar/"
    testar_raspagem_direta(url)
    
