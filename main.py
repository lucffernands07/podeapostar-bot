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

def buscar_gols_pelas_linhas_contadas(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
    print(f"🌐 Acessando Gols: {url}")
    driver.get(url)
    time.sleep(15) # Tempo essencial para carregar as 400+ linhas
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    res = {"+1.5": "N/A", "+2.5": "N/A", "-4.5": "N/A"}
    
    # Ajuste do índice (Sua contagem - 1)
    # Betano 1.5 (132 -> 131), 2.5 (210 -> 209), 4.5 (418 -> 417)
    mapeamento = {
        "+1.5": 131,
        "+2.5": 209,
        "-4.5": 417
    }
    
    for mercado, idx in mapeamento.items():
        try:
            if idx < len(linhas):
                linha = linhas[idx]
                spans = linha.find_elements(By.TAG_NAME, "span")
                dados = [s.text for s in spans if s.text]
                
                # Se for +1.5 ou +2.5, pegamos a odd ACIMA (dados[1])
                # Se for -4.5, pegamos a odd ABAIXO (dados[2])
                if "-" in mercado:
                    res[mercado] = dados[2] if len(dados) >= 3 else "Erro Coluna"
                else:
                    res[mercado] = dados[1] if len(dados) >= 2 else "Erro Coluna"
                
                print(f"📍 Linha {idx+1} ({mercado}): {dados}")
        except Exception as e:
            print(f"⚠️ Erro na linha {idx+1}: {e}")
            
    return res

def buscar_mercado_simples(driver, url, mercado):
    print(f"🌐 Acessando {mercado}: {url}")
    driver.get(url)
    time.sleep(10)
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                valores = [o.text for o in odds if o.text]
                
                if mercado == "BTTS": return valores[0]
                if mercado == "DC": return (valores[0], valores[2])
        except: continue
    return "N/A"

def rodar_teste():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD" # Betis x Real Madrid
    
    try:
        print("🚀 [TESTE] Iniciando captura por índices e lógica de spans...")
        
        # Gols
        gols = buscar_gols_pelas_linhas_contadas(driver, id_jogo)
        
        # BTTS (Lógica validada pelos seus prints)
        btts = buscar_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "BTTS")
        
        # DC (Lógica validada pelos seus prints)
        dc_1x, dc_x2 = buscar_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DC")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL DO TESTE")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols['+1.5']}")
        print(f"🔥 Gols +2.5:  {gols['+2.5']}")
        print(f"❄️ Gols -4.5:  {gols['-4.5']}")
        print(f"🤝 BTTS Sim:   {btts}")
        print(f"🏠 Double 1X:  {dc_1x}")
        print(f"🚀 Double X2:  {dc_x2}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste()
    
