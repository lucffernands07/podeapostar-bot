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

def buscar_bloco_gols(id_jogo):
    """Sessão isolada para o mercado de Gols (Lógica Bingo)"""
    driver = configurar_driver()
    url = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    print(f"🚀 [Sessão A] Iniciando Gols: {url}", flush=True)
    resultado = "N/A"
    try:
        driver.get(url)
        time.sleep(15) # Tempo humano para carga pesada
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            if "1.5" in linha.text:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    spans = linha.find_elements(By.TAG_NAME, "span")
                    dados = [s.text for s in spans if s.text]
                    resultado = dados[1] if len(dados) > 1 else "N/A"
                    break
    finally:
        driver.quit() # Fecha o navegador e limpa tudo
    return resultado

def buscar_bloco_odds_especificas(id_jogo):
    """Sessão isolada para BTTS e Dupla Chance (Lógica dos Prints)"""
    driver = configurar_driver()
    print(f"🌐 [Sessão B] Iniciando BTTS e Dupla Chance...", flush=True)
    res = {"BTTS": "N/A", "1X": "N/A", "X2": "N/A"}
    try:
        # BTTS
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/")
        time.sleep(12)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            try:
                if "Betano" in linha.find_element(By.TAG_NAME, "img").get_attribute("alt"):
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if odds: res["BTTS"] = odds[0]
                    break
            except: continue
        
        # DUPLA CHANCE
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/")
        time.sleep(12)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            try:
                if "Betano" in linha.find_element(By.TAG_NAME, "img").get_attribute("alt"):
                    odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                    if len(odds) >= 3:
                        res["1X"] = odds[0]
                        res["X2"] = odds[2]
                    break
            except: continue
    finally:
        driver.quit() # Fecha o navegador e limpa tudo
    return res

if __name__ == "__main__":
    ID_JOGO = "W8mj7MDD"
    
    # Executa cada bloco de forma independente
    valor_gols = buscar_bloco_gols(ID_JOGO)
    outros_mercados = buscar_bloco_odds_especificas(ID_JOGO)

    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL (EXECUÇÃO EM SESSÕES LIMPAS)")
    print("="*40)
    print(f"🔥 Gols +1.5:  {valor_gols}")
    print(f"🤝 BTTS Sim:   {outros_mercados['BTTS']}")
    print(f"🏠 Double 1X:  {outros_mercados['1X']}")
    print(f"🚀 Double X2:  {outros_mercados['X2']}")
    print("="*40, flush=True)
    
