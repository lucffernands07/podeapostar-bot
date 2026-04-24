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
    options.add_argument("--window-size=1920,3000") # Janela bem alta para ver mais linhas
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def buscar_gols_com_scroll(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
    print(f"🌐 Acessando Gols com Scroll: {url}", flush=True)
    driver.get(url)
    
    # --- TRUQUE DO SCROLL ---
    # Rola 3 vezes para garantir que as 400+ linhas carreguem
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 2000);")
        time.sleep(3)
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    print(f"📊 Total de linhas carregadas após scroll: {len(linhas)}", flush=True)

    res = {"+1.5": "N/A", "+2.5": "N/A", "-4.5": "N/A"}
    mapeamento = {"+1.5": 131, "+2.5": 209, "-4.5": 417}
    
    for mercado, idx in mapeamento.items():
        try:
            if idx < len(linhas):
                linha = linhas[idx]
                spans = linha.find_elements(By.TAG_NAME, "span")
                dados = [s.text for s in spans if s.text]
                
                if "-" in mercado:
                    res[mercado] = dados[2] if len(dados) >= 3 else "N/A"
                else:
                    res[mercado] = dados[1] if len(dados) >= 2 else "N/A"
                print(f"📍 Confirmando Linha {idx+1} ({mercado}): {dados}", flush=True)
        except: continue
    return res

def buscar_mercado_simples(driver, url, mercado):
    driver.get(url)
    time.sleep(8)
    # Scroll curto para mercados simples
    driver.execute_script("window.scrollTo(0, 500);")
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    for linha in linhas:
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                valores = [o.text for o in odds if o.text]
                if mercado == "BTTS" and len(valores) >= 1: return valores[0]
                if mercado == "DC" and len(valores) >= 3: return valores[0], valores[2]
        except: continue
    return "N/A" if mercado == "BTTS" else ("N/A", "N/A")

def rodar_teste():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        print("🚀 [TESTE V4] Iniciando com Scroll de carregamento...", flush=True)
        
        gols = buscar_gols_com_scroll(driver, id_jogo)
        
        btts = buscar_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "BTTS")
        
        res_dc = buscar_mercado_simples(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DC")
        dc_1x, dc_x2 = res_dc if isinstance(res_dc, tuple) else ("N/A", "N/A")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL DO TESTE")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols.get('+1.5')}")
        print(f"🔥 Gols +2.5:  {gols.get('+2.5')}")
        print(f"❄️ Gols -4.5:  {gols.get('-4.5')}")
        print(f"🤝 BTTS Sim:   {btts}")
        print(f"🏠 Double 1X:  {dc_1x}")
        print(f"🚀 Double X2:  {dc_x2}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste()
        
