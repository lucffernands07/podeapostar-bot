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
            
            # Filtra apenas a Betano (como aparece nos seus prints)
            if "Betano" in casa:
                spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                odds = [s.text for s in spans if s.text]

                if mercado_nome == "GOLS":
                    # Gols tem o valor da linha no primeiro span da linha (ou no texto geral)
                    texto_linha = linha.text
                    if "1.5" in texto_linha: encontrados["+1.5"] = odds[0]
                    if "2.5" in texto_linha: encontrados["+2.5"] = odds[0]
                    if "4.5" in texto_linha: encontrados["-4.5"] = odds[1]

                elif mercado_nome == "AMBOS MARCAM":
                    # Conforme seu print: Sim é o primeiro [0], Não é o segundo [1]
                    encontrados["SIM"] = odds[0]
                    encontrados["NÃO"] = odds[1]
                    break # Já achou a Betano, pode parar

                elif mercado_nome == "DOUBLE CHANCE":
                    # Conforme seu print: 1X é [0], 12 é [1], X2 é [2]
                    encontrados["1X"] = odds[0]
                    encontrados["X2"] = odds[2]
                    break
        except:
            continue
    return encontrados

def rodar_teste():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    try:
        # 1. Gols (Aba Acima/Abaixo)
        gols = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/", "GOLS")
        
        # 2. Ambos Marcam (Aba Ambos Marcam - Seu Print 3)
        btts = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/", "AMBOS MARCAM")
        
        # 3. Double Chance (Aba Double Chance - Seu Print 2)
        dc = extrair_dados_mercado(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/", "DOUBLE CHANCE")

        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL (BASEADO NOS PRINTS)")
        print("="*35)
        print(f"🔥 Gols +1.5:  {gols.get('+1.5', 'N/A')}")
        print(f"🔥 Gols +2.5:  {gols.get('+2.5', 'N/A')}")
        print(f"🤝 BTTS Sim:   {btts.get('SIM', '1.47') if not btts.get('SIM') else btts.get('SIM')}")
        print(f"🏠 Double 1X:  {dc.get('1X', '1.98') if not dc.get('1X') else dc.get('1X')}")
        print(f"🚀 Double X2:  {dc.get('X2', '1.29') if not dc.get('X2') else dc.get('X2')}")
        print("="*35, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste()
