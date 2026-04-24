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

def extrair_gols_bingo(driver, id_jogo):
    # URL com o parâmetro mid que você validou no código do Bingo
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    print(f"🔍 Buscando Gols (Lógica Bingo): {url}", flush=True)
    driver.get(url)
    
    wait = WebDriverWait(driver, 25)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table")))
    time.sleep(10) 
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    for linha in linhas:
        try:
            conteudo_bruto = linha.text
            if "1.5" in conteudo_bruto:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    spans = linha.find_elements(By.TAG_NAME, "span")
                    textos_span = [s.text for s in spans if s.text]
                    return textos_span[1] if len(textos_span) > 1 else "N/A"
        except: continue
    return "N/A"

def extrair_mercado_simples(driver, url, mercado_nome):
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    driver.get(url)
    time.sleep(12) 
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                odds = [s.text for s in spans if s.text]
                
                if mercado_nome == "BTTS":
                    return odds[0] if odds else "N/A"
                elif mercado_nome == "DC":
                    return (odds[0], odds[2]) if len(odds) >= 3 else ("N/A", "N/A")
        except: continue
    return "N/A" if mercado_nome == "BTTS" else ("N/A", "N/A")

def rodar_unificado():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        # 1. Gols +1.5 usando a lógica do Diagnóstico Bruto
        odd_gols = extrair_gols_bingo(driver, id_jogo)
        
        # 2. BTTS usando a lógica do segundo código
        odd_btts = extrair_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "BTTS")
        
        # 3. Double Chance usando a lógica do segundo código
        odd_1x, odd_x2 = extrair_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DC")

        print("\n" + "="*35)
        print("📊 RELATÓRIO UNIFICADO (LÓGICAS DE SUCESSO)")
        print("="*35)
        print(f"🔥 Gols +1.5:  {odd_gols}")
        print(f"🤝 BTTS Sim:   {odd_btts}")
        print(f"🏠 Double 1X:  {odd_1x}")
        print(f"🚀 Double X2:  {odd_x2}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_unificado()
    
