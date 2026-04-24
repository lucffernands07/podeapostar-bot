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
    options.add_argument("--window-size=1920,3500") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

# --- FUNÇÃO 1: EXCLUSIVA PARA GOLS (Lógica do Bingo + Linhas Exatas) ---
def buscar_gols_por_indice(driver, id_jogo):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
    driver.get(url)
    # Scroll pesado porque a Betano está lá nas linhas 132, 210 e 418
    driver.execute_script("window.scrollTo(0, 3500);")
    time.sleep(15)
    
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    res = {"+1.5": "N/A", "+2.5": "N/A", "-4.5": "N/A"}
    
    # Seus índices contados (Linha - 1)
    mapeamento = {"+1.5": 131, "+2.5": 209, "-4.5": 417}
    
    for mercado, idx in mapeamento.items():
        try:
            if idx < len(linhas):
                spans = linhas[idx].find_elements(By.TAG_NAME, "span")
                dados = [s.text for s in spans if s.text]
                # Lógica do Bingo: Acima é dados[1], Abaixo é dados[2]
                if "-" in mercado: res[mercado] = dados[2]
                else: res[mercado] = dados[1]
        except: continue
    return res

# --- FUNÇÃO 2: EXCLUSIVA PARA BTTS E DC (Lógica dos Prints) ---
def buscar_mercado_por_nome(driver, url, mercado):
    driver.get(url)
    time.sleep(10)
    linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
    
    for linha in linhas:
        try:
            # Busca o nome da casa na imagem (como nos seus prints)
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            if "Betano" in casa:
                # Usa o data-testid que a gente viu que funciona para essas tabelas simples
                odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                valores = [o.text for o in odds if o.text]
                if mercado == "BTTS": return valores[0]
                if mercado == "DC": return valores[0], valores[2]
        except: continue
    return "N/A"

def rodar_teste_final():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        print("🚀 Iniciando extração com lógicas TOTALMENTE separadas...", flush=True)
        
        # Chama Gols com a função de índice
        gols = buscar_gols_por_indice(driver, id_jogo)
        
        # Chama BTTS e DC com a função de nome
        btts = buscar_mercado_por_nome(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "BTTS")
        
        res_dc = buscar_mercado_por_nome(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DC")
        dc_1x, dc_x2 = res_dc if isinstance(res_dc, tuple) else ("N/A", "N/A")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL UNIFICADO")
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
    rodar_teste_final()
        
