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
    """Sessão 1: BTTS e Dupla Chance (Busca Betano ou bet365)"""
    driver = configurar_driver()
    print(f"🌐 [Sessão 1] Buscando BTTS e Dupla Chance...", flush=True)
    res = {"BTTS": "N/A", "1X": "N/A", "X2": "N/A"}
    casas_alvo = ["Betano", "bet365"]
    
    try:
        # --- AMBOS MARCAM ---
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/")
        time.sleep(15)
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            try:
                nome_casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if any(alvo in nome_casa for alvo in casas_alvo):
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if odds:
                        res["BTTS"] = odds[0]
                        print(f"✅ BTTS encontrado ({nome_casa}): {res['BTTS']}", flush=True)
                        break
            except: continue

        # --- DOUBLE CHANCE ---
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/")
        time.sleep(12)
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            try:
                nome_casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if any(alvo in nome_casa for alvo in casas_alvo):
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if len(odds) >= 3:
                        res["1X"] = odds[0]
                        res["X2"] = odds[2]
                        print(f"✅ DC encontrado ({nome_casa}): {res['1X']} / {res['X2']}", flush=True)
                        break
            except: continue
    finally:
        driver.quit()
    return res

def buscar_bloco_gols(id_jogo):
    """Sessão 2: Gols (Lógica Bingo)"""
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
                    nome_casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    if "Betano" in nome_casa or "bet365" in nome_casa:
                        spans = linha.find_elements(By.TAG_NAME, "span")
                        dados = [s.text for s in spans if s.text]
                        resultado = dados[1] if len(dados) > 1 else "N/A"
                        print(f"✅ Gols encontrado ({nome_casa}): {resultado}", flush=True)
                        break
                except: continue
    finally:
        driver.quit()
    return resultado

if __name__ == "__main__":
    ID = "W8mj7MDD"
    
    # Executa as sessões de forma totalmente independente
    odds_principais = buscar_bloco_odds_especificas(ID)
    odd_gols = buscar_bloco_gols(ID)

    print("\n" + "="*45)
    print("📊 RELATÓRIO FINAL - BETANO/BET365")
    print("="*45)
    print(f"🤝 BTTS Sim:   {odds_principais['BTTS']}")
    print(f"🏠 Double 1X:  {odds_principais['1X']}")
    print(f"🚀 Double X2:  {odds_principais['X2']}")
    print(f"🔥 Gols +1.5:  {odd_gols}")
    print("="*45, flush=True)
    
