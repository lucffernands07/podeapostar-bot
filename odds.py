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

# --- 1. AJUSTE NA ASSINATURA: Agora recebe id, t1_url e t2_url ---
def capturar_todas_as_odds(id_jogo, t1_url, t2_url):
    driver = configurar_driver()
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A"
    }
    
    try:
        # --- 2. URL MONTADA CONFORME O SEU TESTE ---
        url_gols = f"https://www.flashscore.com.br/jogo/{t1_url}-v-{t2_url}-{id_jogo}/odds/acima-abaixo/tempo-regulamentar"
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(7)
            
            linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha in linhas_gols:
                txt = linha.text
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                if len(spans) < 2: continue

                if res["GOLS_15"] == "N/A" and "1.5" in txt:
                    for s in spans:
                        if "." in s and s != "1.5":
                            res["GOLS_15"] = s
                            break
                
                elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                    for s in spans:
                        if "." in s and s != "2.5":
                            res["GOLS_25"] = s
                            break

                elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                    decimais = [s for s in spans if "." in s and s != "4.5"]
                    if len(decimais) >= 2:
                        res["GOLS_M45"] = decimais[1] # Odd do "Abaixo"
                        break
        except Exception as e:
            print(f"⚠️ Erro Gols ({id_jogo}): {e}")

        # --- 3. BTTS ---
        try:
            url_btts = f"https://www.flashscore.com.br/jogo/{t1_url}-v-{t2_url}-{id_jogo}/odds/ambos-marcam/tempo-regulamentar"
            driver.get(url_btts)
            time.sleep(8)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if odds_b: res["BTTS"] = odds_b[0]
        except: pass

        # --- 4. DUPLA CHANCE ---
        try:
            url_dc = f"https://www.flashscore.com.br/jogo/{t1_url}-v-{t2_url}-{id_jogo}/odds/double-chance/tempo-regulamentar"
            driver.get(url_dc)
            time.sleep(8)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0]
                res["X2"] = odds_d[2]
        except: pass

    finally:
        driver.quit()
    
    return res
                
