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
            # Pega o nome da casa (ALT da imagem)
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
            
            # Filtra apenas a Betano
            if "Betano" in casa:
                # Usa a lógica de SPAN para GOLS (Bingo) e wcl-oddsValue para o resto
                if mercado_nome == "GOLS":
                    if "1.5" in linha.text:
                        spans = linha.find_elements(By.TAG_NAME, "span")
                        dados = [s.text for s in spans if s.text]
                        encontrados["+1.5"] = dados[1] if len(dados) > 1 else "N/A"
                        break
                
                else:
                    spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    odds = [s.text for s in spans if s.text]

                    if mercado_nome == "AMBOS MARCAM":
                        encontrados["SIM"] = odds[0]
                        encontrados["NÃO"] = odds[1]
                        break

                    elif mercado_nome == "DOUBLE CHANCE":
                        encontrados["1X"] = odds[0]
                        encontrados["X2"] = odds[2]
                        break
        except:
            continue
    return encontrados

def rodar_unificado_final():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        # 1. Gols (Aba Bingo) - Usando a URL completa que você validou
        url_bingo = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
        gols = extrair_dados_mercado(driver, url_bingo, "GOLS")
        
        # 2. Ambos Marcam
        btts = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "AMBOS MARCAM")
        
        # 3. Double Chance
        dc = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DOUBLE CHANCE")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL UNIFICADO")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols.get('+1.5', 'N/A')}")
        print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
        print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
        print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_unificado_final()
    
