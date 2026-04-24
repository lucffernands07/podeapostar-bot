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
    # User-agent para ele não desconfiar que é um robô
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def rodar_extracao_continua():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    res = {"+1.5": "N/A", "BTTS": "N/A", "1X": "N/A", "X2": "N/A"}

    try:
        # --- MERCADO 1: GOLS (A Lógica do seu Bingo) ---
        url_gols = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
        print(f"🚀 Carregando Gols: {url_gols}", flush=True)
        driver.get(url_gols)
        time.sleep(15) # Espera robusta para o JS montar a tabela
        
        # Sua lógica de varredura por texto
        linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas:
            if "1.5" in linha.text:
                try:
                    casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                    if "Betano" in casa:
                        spans = linha.find_elements(By.TAG_NAME, "span")
                        dados = [s.text for s in spans if s.text]
                        res["+1.5"] = dados[1] if len(dados) > 1 else "N/A"
                        break
                except: continue

        # --- MERCADO 2: BTTS (Lógica DP) ---
        # Não fechamos o driver, apenas navegamos para a próxima
        url_btts = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
        print(f"🌐 Mudando para BTTS...", flush=True)
        driver.get(url_btts)
        time.sleep(12)
        
        # Truque: Scroll para forçar o carregamento das imagens (o "alt" da Betano)
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(3)

        linhas_btts = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_btts:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if odds:
                        res["BTTS"] = odds[0].text
                        break
            except: continue

        # --- MERCADO 3: DUPLA CHANCE (Lógica DP) ---
        url_dc = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
        print(f"🌐 Mudando para Dupla Chance...", flush=True)
        driver.get(url_dc)
        time.sleep(12)
        
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(3)

        linhas_dc = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        for linha in linhas_dc:
            try:
                casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
                if "Betano" in casa:
                    odds = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                    if len(odds) >= 3:
                        res["1X"] = odds[0].text
                        res["X2"] = odds[2].text
                        break
            except: continue

        # --- RELATÓRIO FINAL ---
        print("\n" + "="*35)
        print("📊 RELATÓRIO FINAL UNIFICADO")
        print("="*35)
        print(f"🔥 Gols +1.5:  {res['+1.5']}")
        print(f"🤝 BTTS Sim:   {res['BTTS']}")
        print(f"🏠 Double 1X:  {res['1X']}")
        print(f"🚀 Double X2:  {res['X2']}")
        print("="*35, flush=True)

    finally:
        # Agora sim, fechamos tudo no final
        driver.quit()

if __name__ == "__main__":
    rodar_extracao_continua()
    
