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

# --- SEU CÓDIGO COM ESPERA EXPLÍCITA ---
def extrair_dados_mercado(driver, url, mercado_nome):
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    driver.get(url)
    
    # Espera até 20 segundos para a tabela de odds carregar no GitHub
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
    except:
        print(f"⚠️ Tabela não carregou a tempo para {mercado_nome}")

    time.sleep(5) # Delay extra para garantir as imagens
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    encontrados = {}

    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            
            if "Betano" in casa or "bet365" in casa:
                spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                odds = [s.text for s in spans if s.text]

                if mercado_nome == "AMBOS MARCAM":
                    if odds: encontrados["SIM"] = odds[0]
                    break 

                elif mercado_nome == "DOUBLE CHANCE":
                    if len(odds) >= 3:
                        encontrados["1X"] = odds[0]
                        encontrados["X2"] = odds[2]
                    break
        except:
            continue
    return encontrados

# --- SUA LÓGICA DE GOLS (BINGO) ---
def buscar_gols_bingo(id_jogo):
    driver = configurar_driver()
    url = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    print(f"🚀 Iniciando Gols (Lógica Bingo): {url}", flush=True)
    resultado = "N/A"
    try:
        driver.get(url)
        time.sleep(15)
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            if "1.5" in linha.text:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa or "bet365" in casa:
                    spans = linha.find_elements(By.TAG_NAME, "span")
                    textos = [s.text for s in spans if s.text]
                    resultado = textos[1]
                    break
    finally:
        driver.quit()
    return resultado

if __name__ == "__main__":
    ID = "W8mj7MDD"
    
    # Sessão 1: BTTS e DP
    driver_1 = configurar_driver()
    try:
        btts = extrair_dados_mercado(driver_1, f"https://www.flashscore.com.br/jogo/{ID}/odds/ambos-marcam/tempo-regulamentar/", "AMBOS MARCAM")
        dc = extrair_dados_mercado(driver_1, f"https://www.flashscore.com.br/jogo/{ID}/odds/double-chance/tempo-regulamentar/", "DOUBLE CHANCE")
    finally:
        driver_1.quit()

    # Sessão 2: GOLS
    odd_gols = buscar_gols_bingo(ID)

    print("\n" + "="*35)
    print("📊 RELATÓRIO FINAL UNIFICADO")
    print("="*35)
    print(f"🔥 Gols +1.5:  {odd_gols}")
    print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
    print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
    print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
    print("="*35, flush=True)
