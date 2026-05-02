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
    # User-agent para evitar que o site esconda dados de automação
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def testar_raspagem_direta(url_exata):
    driver = configurar_driver()
    
    print(f"--- PASSO 1: Acessando URL Direta ---")
    print(f"URL: {url_exata}")
    
    try:
        driver.get(url_exata)
        wait = WebDriverWait(driver, 15)
        
        # Espera as linhas da tabela carregarem totalmente
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(3) # Tempo para garantir renderização dos spans wcl-oddsValue
        
        print(f"\n--- PASSO 2: Raspagem (Segunda Ocorrência via data-testid) ---")
        
        # Mercados configurados conforme sua necessidade
        alvos = {
            "GOLS_15": {"valor": "1.5", "coluna": 0}, # Acima
            "GOLS_25": {"valor": "2.5", "coluna": 0}, # Acima
            "GOLS_M45": {"valor": "4.5", "coluna": 1}  # Abaixo
        }
        
        resultados = {}

        for chave, config in alvos.items():
            valor = config["valor"]
            col_idx = config["coluna"]
            
            # XPath CIRÚRGICO: 
            # 1. Acha o span com o data-testid que você extraiu e o texto exato.
            # 2. Sobe para a div ancestral que é a linha da tabela (.ui-table__row).
            xpath_linha = f"//div[contains(@class, 'ui-table__row')][.//span[@data-testid='wcl-oddsValue' and text()='{valor}']]"
            
            linhas = driver.find_elements(By.XPATH, xpath_linha)
            
            print(f"Buscando {valor}... Encontradas {len(linhas)} linhas.")

            if len(linhas) >= 2:
                # Pegamos a segunda ocorrência (índice 1) para evitar a primeira casa
                segunda_linha = linhas[1]
                
                # Busca as odds (tags <a>) dentro dessa linha específica
                odds = segunda_linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                
                if len(odds) >= 2:
                    valor_odd = odds[col_idx].text.strip()
                    # Limpeza simples caso tenha setas de variação
                    valor_odd = valor_odd.replace('↑', '').replace('↓', '').strip()
                    
                    resultados[chave] = valor_odd
                    tipo = "Acima" if col_idx == 0 else "Abaixo"
                    print(f"✅ Mercado {valor} ({tipo}): Segunda linha encontrada -> Odd: {valor_odd}")
                else:
                    print(f"⚠️ Erro: Encontrei a linha do {valor}, mas as odds não estão lá.")
            else:
                print(f"❌ Erro: Não encontrei pelo menos 2 linhas para o mercado {valor}")

        print(f"\n--- RESULTADO FINAL ---")
        print(resultados)

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # URL do jogo Botafogo x Remo (Acima/Abaixo)
    url = "https://www.flashscore.com.br/jogo/futebol/botafogo-jXzWoWa5/remo-2i0B6Zul/odds/acima-abaixo/tempo-regulamentar/"
    testar_raspagem_direta(url)
            
