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
    # User-agent para evitar bloqueios no GitHub Actions
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def capturar_todas_as_odds(id_jogo):
    """
    Esta função será chamada pelo seu main.py
    Exemplo: valores = odds.capturar_todas_as_odds("W8mj7MDD")
    """
    driver = configurar_driver()
    # Dicionário padrão para não quebrar o main se algo falhar
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A"
    }
    
    try:
        # --- 1. MERCADO DE GOLS (Lógica Sequencial Validada) ---
        url_gols = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(6)
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            
            for linha in linhas:
                txt = linha.text
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                if len(spans) < 2: continue

                # Busca 1.5
                if res["GOLS_15"] == "N/A" and "1.5" in txt:
                    for s in spans:
                        if "." in s and s != "1.5": res["GOLS_15"] = s; break
                
                # Busca 2.5
                elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                    for s in spans:
                        if "." in s and s != "2.5": res["GOLS_25"] = s; break

                # Busca 4.5
                elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                    decimais = [s for s in spans if "." in s and s != "4.5"]
                    if len(decimais) >= 2: res["GOLS_M45"] = decimais[1]; break
        except:
            print(f"⚠️ Erro ao processar Gols para {id_jogo}")

        # --- 2. BTTS ---
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(6)
        try:
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if odds_b: res["BTTS"] = odds_b[0]
        except: pass

        # --- 3. DUPLA CHANCE ---
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(6)
        try:
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0]
                res["X2"] = odds_d[2]
        except: pass

    finally:
        driver.quit() # Crucial para não travar o GitHub Actions
    
    return res
                        
