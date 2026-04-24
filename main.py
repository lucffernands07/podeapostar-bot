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

def buscar_dados_completos():
    driver = configurar_driver()
    ID = "W8mj7MDD"
    res = {
        "GOLS_15": "N/A", 
        "GOLS_25": "N/A", 
        "GOLS_M45": "N/A", 
        "BTTS": "N/A", 
        "1X": "N/A", 
        "X2": "N/A"
    }
    
    try:
        # 1. MERCADO DE GOLS (Varredura para 1.5, 2.5 e 4.5)
        print("🌐 Escaneando Tabela de Gols (300+ linhas)...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU")
        
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(5)
        
        linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        for linha in linhas_gols:
            txt = linha.text
            # Se acharmos a linha, pegamos os spans de odds
            spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
            
            if "1.5" in txt and res["GOLS_15"] == "N/A":
                if len(spans) >= 2: res["GOLS_15"] = spans[1]
            
            elif "2.5" in txt and res["GOLS_25"] == "N/A":
                if len(spans) >= 2: res["GOLS_25"] = spans[1]
            
            elif "4.5" in txt and res["GOLS_M45"] == "N/A":
                # Para o "Menos 4.5", pegamos a odd da direita (geralmente o último span)
                if len(spans) >= 3: res["GOLS_M45"] = spans[2]

        # 2. BUSCA BTTS
        print("🌐 Buscando BTTS...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/ambos-marcam/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_btts = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_btts = [s.text for s in linha_btts.find_elements(By.TAG_NAME, "span") if s.text]
        if odds_btts: res["BTTS"] = odds_btts[0]

        # 3. BUSCA DUPLA CHANCE
        print("🌐 Buscando Dupla Chance...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/double-chance/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_dc = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_dc = [s.text for s in linha_dc.find_elements(By.TAG_NAME, "span") if s.text]
        if len(odds_dc) >= 3:
            res["1X"] = odds_dc[0]
            res["X2"] = odds_dc[2]

    finally:
        driver.quit()
    return res

if __name__ == "__main__":
    resultado = buscar_dados_completos()
    
    print("\n" + "="*40)
    print("📊 RELATÓRIO EXPANDIDO - BINGO TOTAL")
    print("="*40)
    print(f"🔥 Acima 1.5:  {resultado['GOLS_15']}")
    print(f"🔥 Acima 2.5:  {resultado['GOLS_25']}")
    print(f"🧊 Menos 4.5:  {resultado['GOLS_M45']}")
    print(f"🤝 BTTS Sim:   {resultado['BTTS']}")
    print(f"🏠 Double 1X:  {resultado['1X']}")
    print(f"🚀 Double X2:  {resultado['X2']}")
    print("="*40, flush=True)
    
