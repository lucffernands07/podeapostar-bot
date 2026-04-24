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

def buscar_na_tabela(driver, url, alvos, nome_mercado):
    print(f"\n🌐 Acessando {nome_mercado}: {url}", flush=True)
    driver.get(url)
    time.sleep(10) # Tempo para o Flashscore carregar as centenas de linhas
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    resultados = {}

    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" not in casa:
                continue
            
            spans = linha.find_elements(By.TAG_NAME, "span")
            dados = [s.text for s in spans if s.text]

            # Lógica para Gols (+1.5, +2.5, -4.5)
            if nome_mercado == "GOLS":
                for alvo in alvos:
                    if alvo in dados:
                        tipo = "ACIMA" if "-" not in alvo else "ABAIXO"
                        idx = 1 if tipo == "ACIMA" else 2
                        resultados[f"{tipo} {alvo}"] = dados[idx]
            
            # Lógica para Ambos Marcam
            elif nome_mercado == "BTTS":
                resultados["BTTS SIM"] = dados[0]
                resultados["BTTS NÃO"] = dados[1]
                break # BTTS só tem uma linha por casa

            # Lógica para Dupla Chance
            elif nome_mercado == "DC":
                resultados["1X"] = dados[0]
                resultados["2X"] = dados[2]
                break

        except:
            continue
    
    return resultados

def testar_tudo():
    driver = configurar_driver()
    base_url = "https://www.flashscore.com.br/jogo/W8mj7MDD/odds/"
    
    try:
        # 1. Testando Gols
        gols = buscar_na_tabela(driver, base_url + "acima-abaixo/tempo-regulamentar/", ["1.5", "2.5", "4.5"], "GOLS")
        
        # 2. Testando Ambos Marcam
        btts = buscar_na_tabela(driver, base_url + "ambos-marcam/tempo-regulamentar/", [], "BTTS")
        
        # 3. Testando Dupla Chance
        dc = buscar_na_tabela(driver, base_url + "double-chance/tempo-regulamentar/", [], "DC")

        print("\n" + "="*30)
        print("📊 RELATÓRIO FINAL (BETANO)")
        print("="*30)
        print(f"🔥 +1.5 Gols: {gols.get('ACIMA 1.5', 'N/A')}")
        print(f"🔥 +2.5 Gols: {gols.get('ACIMA 2.5', 'N/A')}")
        print(f"❄️ -4.5 Gols: {gols.get('ABAIXO 4.5', 'N/A')}")
        print(f"🤝 BTTS Sim:  {btts.get('BTTS SIM', 'N/A')}")
        print(f"🏠 1X (Casa):  {dc.get('1X', 'N/A')}")
        print(f"🚀 2X (Fora):  {dc.get('2X', 'N/A')}")
        print("="*30, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    testar_tudo()
