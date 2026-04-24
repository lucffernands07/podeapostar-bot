import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def configurar_driver_anonimo():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # ATIVAÇÃO DO MODO ANÓNIMO
    options.add_argument("--incognito") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def buscar_btts_e_dc(id_jogo):
    """MOTOR 1: BTTS e DP em Navegador Anónimo"""
    driver = configurar_driver_anonimo()
    res = {"SIM": "N/A", "1X": "N/A", "X2": "N/A"}
    
    url_btts = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
    url_dc = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/double-chance/tempo-regulamentar/"
    
    try:
        # BTTS
        print(f"🌐 [Sessão 1 - Anónima] Verificando BTTS...", flush=True)
        driver.get(url_btts)
        time.sleep(15)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "Betano" in linha.text or "bet365" in linha.text:
                odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                if odds: res["SIM"] = odds[0]; break
        
        # DOUBLE CHANCE
        print(f"🌐 [Sessão 1 - Anónima] Verificando Dupla Chance...", flush=True)
        driver.get(url_dc)
        time.sleep(12)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "Betano" in linha.text or "bet365" in linha.text:
                odds = [s.text for s in linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']") if s.text]
                if len(odds) >= 3:
                    res["1X"] = odds[0]
                    res["X2"] = odds[2]
                    break
    finally:
        driver.quit() # Fecha e destrói a sessão anónima
    return res

def buscar_gols_bingo(id_jogo):
    """MOTOR 2: Gols em NOVO Navegador Anónimo"""
    driver = configurar_driver_anonimo()
    url_gols = f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU"
    odd_15 = "N/A"
    try:
        print(f"🚀 [Sessão 2 - Anónima] Iniciando Gols 1.5...", flush=True)
        driver.get(url_gols)
        time.sleep(15)
        for linha in driver.find_elements(By.CSS_SELECTOR, ".ui-table__row"):
            if "1.5" in linha.text and ("Betano" in linha.text or "bet365" in linha.text):
                spans = linha.find_elements(By.TAG_NAME, "span")
                textos = [s.text for s in spans if s.text]
                if len(textos) > 1: odd_15 = textos[1]; break
    finally:
        driver.quit() # Fecha e destrói a segunda sessão anónima
    return odd_15

if __name__ == "__main__":
    ID = "W8mj7MDD"
    
    # Passo 1: BTTS e DP
    dados = buscar_btts_e_dc(ID)
    
    # Critério: Só segue se NÃO houver N/A nos campos obrigatórios
    falhou = any(v == "N/A" for v in [dados["SIM"], dados["1X"], dados["X2"]])
    
    res_gols = "N/A"
    if not falhou:
        # Passo 2: Gols (com navegador novo e anónimo)
        res_gols = buscar_gols_bingo(ID)
    else:
        print("❌ Abortando: Dados de BTTS/DP incompletos.", flush=True)

    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL (MODO ANÓNIMO)")
    print("="*40)
    print(f"🤝 BTTS Sim:   {dados['SIM']}")
    print(f"🏠 Double 1X:  {dados['1X']}")
    print(f"🚀 Double X2:  {dados['X2']}")
    print(f"🔥 Gols +1.5:  {res_gols}")
    print("="*40, flush=True)
        
