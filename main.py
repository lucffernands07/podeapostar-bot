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

def extrair_mercado(url, mercado_nome):
    driver = configurar_driver()
    print(f"🌐 Verificando: {mercado_nome}...", flush=True)
    try:
        driver.get(url)
        # Tempo de espera generoso que você validou
        time.sleep(15) 
        
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        encontrados = {}

        for linha in linhas:
            try:
                # Busca pela imagem da Betano (Lógica dos seus prints)
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                
                if "Betano" in casa:
                    # Lógica específica para GOLS (Bingo - Usando Spans)
                    if mercado_nome == "GOLS":
                        if "1.5" in linha.text:
                            spans = linha.find_elements(By.TAG_NAME, "span")
                            dados = [s.text for s in spans if s.text]
                            encontrados["+1.5"] = dados[1] if len(dados) > 1 else "N/A"
                    
                    # Lógica para BTTS e DC (Usando data-testid)
                    else:
                        spans = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                        odds = [s.text for s in spans if s.text]

                        if mercado_nome == "AMBOS MARCAM":
                            encontrados["SIM"] = odds[0]
                        elif mercado_nome == "DOUBLE CHANCE":
                            encontrados["1X"] = odds[0]
                            encontrados["X2"] = odds[2]
                    break
            except:
                continue
        return encontrados
    finally:
        driver.quit()

def rodar_sequencia_invertida():
    id_jogo = "W8mj7MDD" # Bétis x Real Madrid
    
    # --- 1º: BTTS (Rápido e Estável) ---
    url_btts = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
    btts = extrair_mercado(url_btts, "AMBOS MARCAM")
    
    # --- 2º: DOUBLE CHANCE (Rápido e Estável) ---
    url_dc = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
    dc = extrair_mercado(url_dc, "DOUBLE CHANCE")
    
    # --- 3º: GOLS (Pesado - Lógica Bingo por último) ---
    url_gols = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    gols = extrair_mercado(url_gols, "GOLS")

    print("\n" + "="*35)
    print("📊 RELATÓRIO FINAL (ORDEM INVERTIDA)")
    print("="*35)
    print(f"🤝 BTTS Sim:   {btts.get('SIM', 'N/A')}")
    print(f"🏠 Double 1X:  {dc.get('1X', 'N/A')}")
    print(f"🚀 Double X2:  {dc.get('X2', 'N/A')}")
    print(f"🔥 Gols +1.5:  {gols.get('+1.5', 'N/A')}")
    print("="*35, flush=True)

if __name__ == "__main__":
    rodar_sequencia_invertida()
    
