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

def rodar_extracao_humana():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    res = {"+1.5": "N/A", "BTTS": "N/A", "1X": "N/A", "X2": "N/A"}

    try:
        # --- 1. LÓGICA GOLS (CÓDIGO BINGO) ---
        # Usando a URL exata e o tempo de espera que você validou
        url_gols = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
        print(f"🚀 Iniciando Gols (Lógica Bingo): {url_gols}", flush=True)
        driver.get(url_gols)
        time.sleep(10) 
        
        linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_gols:
            try:
                conteudo_bruto = linha.text
                if "1.5" in conteudo_bruto:
                    casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    if "Betano" in casa:
                        spans = linha.find_elements(By.TAG_NAME, "span")
                        textos_span = [s.text for s in spans if s.text]
                        res["+1.5"] = textos_span[1]
                        break
            except: continue

        # --- 2. LÓGICA BTTS (SEU SEGUNDO CÓDIGO) ---
        url_btts = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
        print(f"🌐 Verificando BTTS: {url_btts}", flush=True)
        driver.get(url_btts)
        time.sleep(12)
        
        linhas_btts = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_btts:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if odds:
                        res["BTTS"] = odds[0].text
                        break
            except: continue

        # --- 3. LÓGICA DUPLA CHANCE (SEU SEGUNDO CÓDIGO) ---
        url_dc = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
        print(f"🌐 Verificando DC: {url_dc}", flush=True)
        driver.get(url_dc)
        time.sleep(12)
        
        linhas_dc = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_dc:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if len(odds) >= 3:
                        res["1X"] = odds[0].text
                        res["X2"] = odds[2].text
                        break
            except: continue

        # --- RELATÓRIO FINAL ---
        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL UNIFICADO")
        print("="*35)
        print(f"🔥 Gols +1.5:  {res['+1.5']}")
        print(f"🤝 BTTS Sim:   {res['BTTS']}")
        print(f"🏠 Double 1X:  {res['1X']}")
        print(f"🚀 Double X2:  {res['X2']}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_extracao_humana()
        
