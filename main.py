import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def rodar_teste_primeira_linha():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        # --- 1. AMBOS MARCAM (BTTS) ---
        print(f"🌐 Verificando Primeira Linha: AMBOS MARCAM...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/")
        time.sleep(12)
        
        try:
            primeira_linha_btts = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            casa_btts = primeira_linha_btts.find_element(By.TAG_NAME, "img").get_attribute("alt")
            odds_btts = [s.text for s in primeira_linha_btts.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
            print(f"✅ BTTS [1ª Linha - {casa_btts}]: {odds_btts}", flush=True)
        except:
            print("❌ Não foi possível ler a primeira linha de BTTS", flush=True)

        # --- 2. DOUBLE CHANCE (DP) ---
        print(f"\n🌐 Verificando Primeira Linha: DOUBLE CHANCE...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/")
        time.sleep(12)
        
        try:
            primeira_linha_dc = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            casa_dc = primeira_linha_dc.find_element(By.TAG_NAME, "img").get_attribute("alt")
            odds_dc = [s.text for s in primeira_linha_dc.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
            print(f"✅ DC [1ª Linha - {casa_dc}]: {odds_dc}", flush=True)
        except:
            print("❌ Não foi possível ler a primeira linha de DC", flush=True)

        # --- 3. ACIMA/ABAIXO (GOLS) ---
        print(f"\n🌐 Verificando JSON da Primeira Linha: GOLS 0.5...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/")
        time.sleep(12)
        
        try:
            primeira_linha_gols = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            # Extraindo todos os dados da linha para o JSON
            casa_gols = primeira_linha_gols.find_element(By.TAG_NAME, "img").get_attribute("alt")
            odds_gols = [s.text for s in primeira_linha_gols.find_elements(By.TAG_NAME, "span") if s.text]
            
            dados_json = {
                "mercado": "Gols 0.5 (Provável)",
                "casa": casa_gols,
                "valores": odds_gols,
                "texto_completo": primeira_linha_gols.text.replace("\n", " ")
            }
            print(f"✅ JSON GOLS: {json.dumps(dados_json, indent=4, ensure_ascii=False)}", flush=True)
        except:
            print("❌ Não foi possível ler a primeira linha de Gols", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste_primeira_linha()
    
