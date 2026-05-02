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
        
        # Mercados que queremos buscar com XPath cirúrgico
        alvos = {
            "GOLS_15": {"valor": "1.5", "coluna": 0}, # Acima
            "GOLS_25": {"valor": "2.5", "coluna": 0}, # Acima
            "GOLS_M45": {"valor": "4.5", "coluna": 1}  # Abaixo
        }
        
        resultados = {}

        for chave, config in alvos.items():
            valor = config["valor"]
            coluna_index = config["coluna"]
            
            # XPath Robusto: Busca a linha (.ui-table__row) que contém
            # uma div descendente cuja div neta tenha o texto exato, ignorando espaços.
            xpath_especifico = f"//div[contains(@class, 'ui-table__row')][.//div/div[normalize-space(text())='{valor}']]"
            
            # Tenta encontrar usando o XPath cirúrgico
            linhas = driver.find_elements(By.XPATH, xpath_especifico)
            
            # Se falhar, usa a busca flexível de texto como backup (o que tínhamos antes)
            if not linhas:
                linhas_todas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
                linhas = [l for l in linhas_todas if valor in l.text]

            if len(linhas) >= 2:
                # Pegamos a segunda linha (índice 1)
                segunda_linha = linhas[1]
                odds = segunda_linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                
                if len(odds) >= 2:
                    odd_valor = odds[coluna_index].text.strip()
                    resultados[chave] = odd_valor
                    print(f"✅ Mercado {valor} encontrado na 2ª linha -> Odd: {odd_valor}")
            else:
                print(f"❌ Erro: Não encontrei 2 ocorrências do mercado {valor}")

    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/botafogo-jXzWoWa5/remo-2i0B6Zul/odds/acima-abaixo/tempo-regulamentar/"
    testar_raspagem_direta(url)
    
