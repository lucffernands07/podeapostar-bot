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

def testar_diagnostico_bruto():
    driver = configurar_driver()
    # URL DIRETA DA ABA ACIMA/ABAIXO
    url = "https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-W8mj7MDD/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    
    try:
        print(f"🚀 Iniciando Diagnóstico Bruto: Bétis x Real Madrid", flush=True)
        driver.get(url)
        
        wait = WebDriverWait(driver, 25)
        # Espera o container principal da tabela
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table")))
        
        print("⏳ Aguardando 10 segundos para carga total do JS...", flush=True)
        time.sleep(10) 
        
        # Pega todas as linhas da tabela
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        print(f"📊 Total de linhas encontradas: {len(linhas)}", flush=True)

        for i, linha in enumerate(linhas):
            conteudo_bruto = linha.text.replace('\n', ' | ')
            print(f"--- Linha {i} ---")
            print(f"TEXTO: {conteudo_bruto}", flush=True)
            
            # Tenta buscar os spans de odds dentro dessa linha específica
            spans = linha.find_elements(By.TAG_NAME, "span")
            textos_span = [s.text for s in spans if s.text]
            print(f"SPANS: {textos_span}", flush=True)

            # Se acharmos qualquer menção a 1.5, analisamos os atributos
            if "1.5" in conteudo_bruto:
                print("🎯 ENCONTRADO GATILHO 1.5 NESSA LINHA!", flush=True)
                html_da_linha = linha.get_attribute('innerHTML')
                # Isso vai mostrar no log se o '1.5' está num data-testid ou outra classe
                print(f"HTML DA LINHA: {html_da_linha[:200]}...", flush=True)

    except Exception as e:
        print(f"⚠️ Erro: {e}", flush=True)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_diagnostico_bruto()
