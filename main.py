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

# 1. CÓDIGO DE GOLS (O que deu BINGO no +1.5)
def buscar_gols(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
    driver.get(url)
    time.sleep(12)
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    res = {"+1.5": "N/A", "+2.5": "N/A", "-4.5": "N/A"}
    
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                spans = linha.find_elements(By.TAG_NAME, "span")
                dados = [s.text for s in spans if s.text]
                # Lógica exata do bingo: dados[0] é o valor da linha (ex: '1.5')
                if "1.5" in dados: res["+1.5"] = dados[1]
                if "2.5" in dados: res["+2.5"] = dados[1]
                if "4.5" in dados: res["-4.5"] = dados[2] # Coluna Abaixo
        except: continue
    return res

# 2. CÓDIGO DE BTTS (Estrutura Sim/Não)
def buscar_btts(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
    driver.get(url)
    time.sleep(10)
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                # No BTTS as odds são diretas nos spans
                odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                return odds[0].text # Retorna o SIM
        except: continue
    return "N/A"

# 3. CÓDIGO DE DUPLA CHANCE (Estrutura 1X - 12 - X2)
def buscar_dc(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
    driver.get(url)
    time.sleep(10)
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                return odds[0].text, odds[2].text # Retorna 1X e X2
        except: continue
    return "N/A", "N/A"

def testar_tudo():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        print("🚀 Iniciando busca por mercados separados...", flush=True)
        
        gols = buscar_gols(driver, id_jogo)
        btts_sim = buscar_btts(driver, id_jogo)
        dc_1x, dc_x2 = buscar_dc(driver, id_jogo)

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL (LÓGICA INDIVIDUAL)")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols['+1.5']}")
        print(f"🔥 Gols +2.5:  {gols['+2.5']}")
        print(f"❄️ Gols -4.5:  {gols['-4.5']}")
        print(f"🤝 BTTS Sim:   {btts_sim}")
        print(f"🏠 Double 1X:  {dc_1x}")
        print(f"🚀 Double X2:  {dc_x2}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    testar_tudo()
