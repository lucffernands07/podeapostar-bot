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

# --- SEU CÓDIGO DE SUCESSO PARA BTTS E DP ---
def extrair_dados_mercado(driver, url, mercado_nome):
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    driver.get(url)
    
    # Espera até 25 segundos para a tabela carregar no GitHub
    try:
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
    except:
        print(f"⚠️ Tabela não apareceu em {mercado_nome}.", flush=True)

    time.sleep(10) 
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    encontrados = {}

    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            
            if "Betano" in casa or "bet365" in casa:
                spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                odds = [s.text for s in spans if s.text]

                if mercado_nome == "AMBOS MARCAM" and odds:
                    encontrados["SIM"] = odds[0]
                    break 

                elif mercado_nome == "DOUBLE CHANCE" and len(odds) >= 3:
                    encontrados["1X"] = odds[0]
                    encontrados["X2"] = odds[2]
                    break
        except:
            continue
    return encontrados

# --- SUA LÓGICA DE GOLS (BINGO) ---
def buscar_gols_bingo(url_gols):
    driver = configurar_driver()
    print(f"🚀 Iniciando Gols: {url_gols}", flush=True)
    resultado = "N/A"
    try:
        driver.get(url_gols)
        time.sleep(15)
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            if "1.5" in linha.text:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa or "bet365" in casa:
                    spans = linha.find_elements(By.TAG_NAME, "span")
                    textos = [s.text for s in spans if s.text]
                    resultado = textos[1] if len(textos) > 1 else "N/A"
                    break
    finally:
        driver.quit()
    return resultado

if __name__ == "__main__":
    ID = "W8mj7MDD"
    
    # URLs Completas conforme padrão do Gols
    url_btts = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/ambos-marcam/tempo-regulamentar/"
    url_dc = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/double-chance/tempo-regulamentar/"
    url_gols = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"

    # --- 1º PASSO: BTTS E DP (Sessão Isolada) ---
    driver_1 = configurar_driver()
    try:
        btts = extrair_dados_mercado(driver_1, url_btts, "AMBOS MARCAM")
        dc = extrair_dados_mercado(driver_1, url_dc, "DOUBLE CHANCE")
    finally:
        driver_1.quit()

    # --- 2º PASSO: GOLS (Sessão Isolada) ---
    odd_gols = buscar_gols_bingo(url_gols)

    print("\n" + "="*35)
    print("📊 RELATÓRIO FINAL UNIFICADO")
    print("="*35)
    print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
    print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
    print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
    print(f"🔥 Gols +1.5:  {odd_gols}")
    print("="*35, flush=True)
