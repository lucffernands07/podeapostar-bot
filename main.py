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

def buscar_btts_e_dc(id_jogo):
    """Usa o seu código que funciona para BTTS e DP"""
    driver = configurar_driver()
    resultados = {"SIM": "N/A", "1X": "N/A", "X2": "N/A"}
    try:
        # BTTS
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/")
        time.sleep(15)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "Betano" in linha.text or "bet365" in linha.text:
                odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                if odds: resultados["SIM"] = odds[0]; break
        
        # Double Chance
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/")
        time.sleep(12)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "Betano" in linha.text or "bet365" in linha.text:
                odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                if len(odds) >= 3: resultados["1X"] = odds[0]; resultados["X2"] = odds[2]; break
    finally:
        driver.quit()
    return resultados

def buscar_gols_bingo(id_jogo):
    """Usa a URL de Bingo que funciona no meu código"""
    driver = configurar_driver()
    url = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    odd_15 = "N/A"
    try:
        driver.get(url)
        time.sleep(15)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "1.5" in linha.text and ("Betano" in linha.text or "bet365" in linha.text):
                spans = linha.find_elements(By.TAG_NAME, "span")
                textos = [s.text for s in spans if s.text]
                if len(textos) > 1: odd_15 = textos[1]; break
    finally:
        driver.quit()
    return odd_15

if __name__ == "__main__":
    ID = "W8mj7MDD"
    print("🚀 Iniciando extração completa...", flush=True)
    
    # Roda BTTS e DP primeiro
    dados_principais = buscar_btts_e_dc(ID)
    
    # Roda Gols depois
    valor_gols = buscar_gols_bingo(ID)

    print("\n" + "="*35)
    print("📊 RELATÓRIO FINAL COMBINADO")
    print("="*35)
    print(f"🔥 Gols +1.5:  {valor_gols}")
    print(f"🤝 BTTS Sim:   {dados_principais['SIM']}")
    print(f"🏠 Double 1X:  {dados_principais['1X']}")
    print(f"🚀 Double X2:  {dados_principais['X2']}")
    print("="*35, flush=True)
