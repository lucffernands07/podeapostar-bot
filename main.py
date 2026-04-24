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

# --- SUA FUNÇÃO DE SUCESSO (BTTS E DP) ---
def extrair_dados_mercado(driver, url, mercado_nome):
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    driver.get(url)
    time.sleep(12) 
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    encontrados = {}

    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            
            # Buscando Betano ou bet365 para garantir o resultado
            if "Betano" in casa or "bet365" in casa:
                spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                odds = [s.text for s in spans if s.text]

                if mercado_nome == "AMBOS MARCAM":
                    encontrados["SIM"] = odds[0]
                    break 

                elif mercado_nome == "DOUBLE CHANCE":
                    encontrados["1X"] = odds[0]
                    encontrados["X2"] = odds[2]
                    break
        except:
            continue
    return encontrados

# --- SUA LÓGICA DE SUCESSO PARA GOLS (BINGO) ---
def buscar_gols_bingo(id_jogo):
    driver = configurar_driver()
    url = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    print(f"🚀 Iniciando Gols (Lógica Bingo): {url}", flush=True)
    res_gols = "N/A"
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
                    res_gols = textos[1]
                    break
    finally:
        driver.quit()
    return res_gols

def rodar_projeto_completo():
    id_jogo = "W8mj7MDD"
    
    # 1. BUSCA BTTS E DP (Sessão Limpa 1 - Seu Código)
    driver_sessao1 = configurar_driver()
    try:
        btts = extrair_dados_mercado(driver_sessao1, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "AMBOS MARCAM")
        dc = extrair_dados_mercado(driver_sessao1, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DOUBLE CHANCE")
    finally:
        driver_sessao1.quit()

    # 2. BUSCA GOLS (Sessão Limpa 2 - Lógica Bingo)
    odd_gols = buscar_gols_bingo(id_jogo)

    # RELATÓRIO FINAL UNIFICADO
    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL UNIFICADO")
    print("="*40)
    print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
    print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
    print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
    print(f"🔥 Gols +1.5:  {odd_gols}")
    print("="*40, flush=True)

if __name__ == "__main__":
    rodar_projeto_completo()
    
