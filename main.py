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

def extrair_dados_mercado(driver, url, mercado_nome):
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    driver.get(url)
    time.sleep(12) 
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    encontrados = {}

    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            
            if "Betano" in casa:
                # Pegamos todos os spans da linha
                spans = linha.find_elements(By.CSS_SELECTOR, "span")
                dados = [s.text.strip() for s in spans if s.text]

                if mercado_nome == "GOLS":
                    # Estrutura observada no seu log: ['1.5', '1.16', '5.00']
                    # O primeiro elemento (dados[0]) é o valor do GOL
                    if "1.5" == dados[0]: encontrados["+1.5"] = dados[1]
                    if "2.5" == dados[0]: encontrados["+2.5"] = dados[1]
                    if "4.5" == dados[0]: encontrados["-4.5"] = dados[2] # Coluna 'Abaixo'

                elif mercado_nome == "AMBOS MARCAM":
                    encontrados["SIM"] = dados[0]
                    break 

                elif mercado_nome == "DOUBLE CHANCE":
                    encontrados["1X"] = dados[0]
                    encontrados["X2"] = dados[2]
                    break
        except:
            continue
    return encontrados

def rodar_teste():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        gols = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/", "GOLS")
        btts = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "AMBOS MARCAM")
        dc = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DOUBLE CHANCE")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL DE TESTE")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols.get('+1.5', 'N/A')}")
        print(f"🔥 Gols +2.5:  {gols.get('+2.5', 'N/A')}")
        print(f"❄️ Gols -4.5:  {gols.get('-4.5', 'N/A')}")
        print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
        print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
        print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste()
