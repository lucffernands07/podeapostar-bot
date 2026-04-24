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

def rodar_extracao_unificada():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD" # Bétis x Real Madrid
    resultados = {"+1.5": "N/A", "BTTS": "N/A", "1X": "N/A", "X2": "N/A"}

    try:
        # --- 1. LÓGICA DO BINGO (GOLS +1.5) ---
        url_gols = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
        print(f"🔍 Buscando +1.5 Gols (Lógica Bingo)...", flush=True)
        driver.get(url_gols)
        time.sleep(12)
        
        linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_gols:
            try:
                # Varre spans exatamente como no código que deu o Bingo
                spans = linha.find_elements(By.TAG_NAME, "span")
                dados = [s.text for s in spans if s.text]
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                
                if "1.5" in dados and "Betano" in casa:
                    resultados["+1.5"] = dados[1]
                    break # Achou o Bingo, para de procurar gols
            except: continue

        # --- 2. LÓGICA DOS PRINTS (BTTS) ---
        url_btts = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
        print(f"🔍 Buscando BTTS (Lógica do Print)...", flush=True)
        driver.get(url_btts)
        time.sleep(10)
        
        linhas_btts = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_btts:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if odds:
                        resultados["BTTS"] = odds[0].text # SIM
                        break
            except: continue

        # --- 3. LÓGICA DOS PRINTS (DOUBLE CHANCE) ---
        url_dc = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
        print(f"🔍 Buscando Dupla Chance (Lógica do Print)...", flush=True)
        driver.get(url_dc)
        time.sleep(10)
        
        linhas_dc = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_dc:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if len(odds) >= 3:
                        resultados["1X"] = odds[0].text
                        resultados["X2"] = odds[2].text
                        break
            except: continue

        # --- RELATÓRIO FINAL UNIFICADO ---
        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL UNIFICADO")
        print("="*35)
        print(f"🔥 Gols +1.5:  {resultados['+1.5']}")
        print(f"🤝 BTTS Sim:   {resultados['BTTS']}")
        print(f"🏠 Double 1X:  {resultados['1X']}")
        print(f"🚀 Double X2:  {resultados['X2']}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_extracao_unificada()
        
