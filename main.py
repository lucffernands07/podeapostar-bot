import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def buscar_dados():
    driver = configurar_driver()
    ID = "W8mj7MDD"
    res = {"GOLS": "N/A", "BTTS": "N/A", "1X": "N/A", "X2": "N/A"}
    
    try:
        # 1. BUSCA GOLS (Varredura profunda para achar a linha 132 ou onde estiver o 1.5)
        print("🌐 Buscando Gols 1.5 (Varredura de tabela)...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU")
        
        # Espera a tabela existir
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(5) # Tempo para o JS carregar as centenas de linhas
        
        linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        print(f"📊 Total de linhas detectadas: {len(linhas_gols)}", flush=True)

        for linha in linhas_gols:
            texto = linha.text
            if "1.5" in texto:
                # Achou a linha do 1.5, agora pega os spans de odds
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                # No seu log, a odd de 'Acima' é o segundo valor numérico que aparece
                # Exemplo: ["1.5", "1.14", "5.50"] -> Queremos o "1.14"
                if len(spans) >= 2:
                    res["GOLS"] = spans[1]
                    print(f"🎯 1.5 Encontrado! Odd: {res['GOLS']}", flush=True)
                    break

        # 2. BUSCA BTTS (Primeira Linha - bet365/Betano)
        print("🌐 Buscando BTTS...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/ambos-marcam/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_btts = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_btts = [s.text for s in linha_btts.find_elements(By.TAG_NAME, "span") if s.text]
        if odds_btts: res["BTTS"] = odds_btts[0]

        # 3. BUSCA DUPLA CHANCE (Primeira Linha - bet365/Betano)
        print("🌐 Buscando Dupla Chance...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/double-chance/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_dc = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_dc = [s.text for s in linha_dc.find_elements(By.TAG_NAME, "span") if s.text]
        if len(odds_dc) >= 3:
            res["1X"] = odds_dc[0]
            res["X2"] = odds_dc[2]

    finally:
        driver.quit()
    return res

if __name__ == "__main__":
    dados = buscar_dados()
    print("\n" + "="*35)
    print("📊 RELATÓRIO FINAL")
    print("="*35)
    print(f"🔥 Gols +1.5:  {dados['GOLS']}")
    print(f"🤝 BTTS Sim:   {dados['BTTS']}")
    print(f"🏠 Double 1X:  {dados['1X']}")
    print(f"🚀 Double X2:  {dados['X2']}")
    print("="*35, flush=True)
    
