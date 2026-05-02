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
    options.add_argument("--headless=new") # Rode sem interface para ser mais rápido
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def testar_raspagem_odds(url_alvo):
    driver = configurar_driver()
    
    print(f"--- PASSO 1: Acessando URL ---")
    print(f"URL: {url_alvo}")
    
    try:
        driver.get(url_alvo)
        wait = WebDriverWait(driver, 15)
        
        # Espera as linhas da tabela carregarem
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(2) # Pausa para garantir que os valores dinâmicos carregaram
        
        print(f"\n--- PASSO 2: Raspagem das Segundas Odds ---")
        
        # Mercados que queremos buscar
        alvos = {
            "1.5": "ACIMA",
            "2.5": "ACIMA",
            "4.5": "ABAIXO"
        }
        
        for valor, tipo in alvos.items():
            # XPath para encontrar as linhas que contém o valor exato (1.5, 2.5, etc)
            # Buscamos o div que contém o texto exato dentro da linha da tabela
            xpath_linhas = f"//div[contains(@class, 'ui-table__row')][.//div[text()='{valor}']]"
            linhas = driver.find_elements(By.XPATH, xpath_linhas)
            
            if len(linhas) >= 2:
                # Pegamos a segunda linha (índice 1) para evitar a primeira casa de apostas
                segunda_linha = linhas[1]
                
                # As odds ficam dentro de tags <a> com a classe 'oddsCell__odd'
                odds = segunda_linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                
                if len(odds) >= 2:
                    if tipo == "ACIMA":
                        # Primeiro odd da linha (Esquerda)
                        odd_valor = odds[0].text.strip()
                        print(f"✅ Mercado {valor} ({tipo}): Segunda linha encontrada -> Odd: {odd_valor}")
                    else:
                        # Segundo odd da linha (Direita)
                        odd_valor = odds[1].text.strip()
                        print(f"✅ Mercado {valor} ({tipo}): Segunda linha encontrada -> Odd: {odd_valor}")
                else:
                    print(f"⚠️ Erro: Encontrei a linha do {valor}, mas não as células de odd.")
            else:
                print(f"❌ Erro: Não encontrei a segunda ocorrência do mercado {valor}")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        print("\n--- Teste Finalizado ---")
        driver.quit()

if __name__ == "__main__":
    # URL enviada do jogo Botafogo x Remo
    url = "https://www.flashscore.com.br/jogo/futebol/botafogo-jXzWoWa5/remo-2i0B6Zul/odds/acima-abaixo/tempo-regulamentar/"
    testar_raspagem_odds(url)
          
