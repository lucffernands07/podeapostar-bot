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

def buscar_bloco_odds_especificas(id_jogo):
    """Sessão B: BTTS e Dupla Chance (Agora rodando primeiro)"""
    driver = configurar_driver()
    print(f"🌐 [Sessão 1] Buscando BTTS e Dupla Chance...", flush=True)
    res = {"BTTS": "N/A", "1X": "N/A", "X2": "N/A"}
    try:
        # BTTS
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/")
        time.sleep(15)
        driver.execute_script("window.scrollTo(0, 600);") # Força renderização das imagens
        time.sleep(3)
        
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if odds: res["BTTS"] = odds[0]
                    break
            except: continue
        
        # DUPLA CHANCE
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/")
        time.sleep(12)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(3)
        
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if len(odds) >= 3:
                        res["1X"] = odds[0]
                        res["X2"] = odds[2]
                    break
            except: continue
    finally:
        driver.quit()
    return res

def buscar_bloco_gols(id_jogo):
    """Sessão A: Gols (Agora rodando por último)"""
    driver = configurar_driver()
    url = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    print(f"🚀 [Sessão 2] Buscando Gols: {url}", flush=True)
    resultado = "N/A"
    try:
        driver.get(url)
        time.sleep(15)
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            if "1.5" in linha.text:
                try:
                    casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    if "Betano" in casa:
                        spans = linha.find_elements(By.TAG_NAME, "span")
                        dados = [s.text for s in spans if s.text]
                        resultado = dados[1] if len(dados) > 1 else "N/A"
                        break
                except: continue
    finally:
        driver.quit()
    return resultado

if __name__ == "__main__":
    ID_JOGO = "W8mj7MDD"
    
    # INVERTIDO: Primeiro o que estava dando N/A
    outros_mercados = buscar_bloco_odds_especificas(ID_JOGO)
    valor_gols = buscar_bloco_gols(ID_JOGO)

    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL (SESSÕES LIMPAS - ORDEM INV)")
    print("="*40)
    print(f"🤝 BTTS Sim:   {outros_mercados['BTTS']}")
    print(f"🏠 Double 1X:  {outros_mercados['1X']}")
    print(f"🚀 Double X2:  {outros_mercados['X2']}")
    print(f"🔥 Gols +1.5:  {valor_gols}")
    print("="*40, flush=True)
        
