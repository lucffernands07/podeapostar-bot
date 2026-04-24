import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def capturar_15_betano():
    driver = configurar_driver()
    # URL direta da aba de gols
    url = "https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-W8mj7MDD/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    
    try:
        print(f"🚀 Iniciando captura Betano: Bétis x Real Madrid", flush=True)
        driver.get(url)
        
        # Espera generosa para garantir as centenas de linhas
        time.sleep(10) 

        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        print(f"📊 Analisando as primeiras linhas...", flush=True)

        for i, linha in enumerate(linhas):
            # Pegamos os textos (Linha, Odd Acima, Odd Abaixo)
            spans = linha.find_elements(By.TAG_NAME, "span")
            dados = [s.text for s in spans if s.text]
            
            # Tentamos pegar o nome da casa (ALT da imagem)
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            except:
                casa = "Desconhecida"

            # Log visual para conferência no GitHub
            if i < 15: # Mostra só as 15 primeiras no log para não poluir
                print(f"Linha {i}: [{casa}] Dados: {dados}", flush=True)

            # CONDIÇÃO BINGO: Linha 1.5 e Casa Betano
            if "1.5" in dados and "Betano" in casa:
                odd_acima = dados[1]
                print(f"\n✅ ENCONTRADO NA LINHA {i}!")
                print(f"💰 Odd Betano (+1.5): {odd_acima}")
                sys.stdout.flush()
                return odd_acima

        print("❌ Não encontramos a linha 1.5 da Betano especificamente.", flush=True)

    except Exception as e:
        print(f"⚠️ Erro: {e}", flush=True)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    capturar_15_betano()
