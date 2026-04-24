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

def buscar_dados_completos():
    driver = configurar_driver()
    ID = "W8mj7MDD"
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A"
    }
    
    try:
        # 1. MERCADO DE GOLS - Progressão por Títulos
        print("🌐 Escaneando Tabela de Gols (Busca Sequencial)...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU")
        
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(7)
        
        linhas_gols = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        for linha in linhas_gols:
            txt = linha.text
            # Captura apenas spans que contenham números (odds ou títulos)
            spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
            
            # Pula linhas vazias ou sem odds
            if len(spans) < 2:
                continue

            # BUSCA 1.5: Se ainda não achou, procura a linha que tem 1.5 e uma odd decimal diferente de 1.5
            if res["GOLS_15"] == "N/A" and "1.5" in txt:
                for s in spans:
                    if "." in s and s != "1.5":
                        res["GOLS_15"] = s
                        print(f"✅ Achou 1.5: {s}. Partindo para o próximo título...", flush=True)
                        break
            
            # BUSCA 2.5: Só foca aqui se o 1.5 já foi preenchido
            elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                for s in spans:
                    if "." in s and s != "2.5":
                        res["GOLS_25"] = s
                        print(f"✅ Achou 2.5: {s}. Partindo para o próximo título...", flush=True)
                        break

            # BUSCA 4.5: Só foca aqui se o 2.5 já foi preenchido
            elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                # Menos de 4.5 costuma ser o último valor da linha
                decimais = [s for s in spans if "." in s and s != "4.5"]
                if len(decimais) >= 2:
                    res["GOLS_M45"] = decimais[1] # Pega a odd do "Abaixo"
                    print(f"✅ Achou -4.5: {res['GOLS_M45']}. Varredura de gols finalizada.", flush=True)
                    break

        # 2. BUSCA BTTS
        print("🌐 Buscando BTTS...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/ambos-marcam/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text]
        if odds_b: res["BTTS"] = odds_b[0]

        # 3. BUSCA DUPLA CHANCE
        print("🌐 Buscando Dupla Chance...", flush=True)
        driver.get(f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{ID}/odds/double-chance/tempo-regulamentar/?mid=lfKIYGgU")
        time.sleep(8)
        linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text]
        if len(odds_d) >= 3:
            res["1X"] = odds_d[0]
            res["X2"] = odds_d[2]

    finally:
        driver.quit()
    return res

if __name__ == "__main__":
    resultado = buscar_dados_completos()
    
    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL - SEQUENCIAL")
    print("="*40)
    print(f"🔥 Acima 1.5:  {resultado['GOLS_15']}")
    print(f"🔥 Acima 2.5:  {resultado['GOLS_25']}")
    print(f"🧊 Menos 4.5:  {resultado['GOLS_M45']}")
    print(f"🤝 BTTS Sim:   {resultado['BTTS']}")
    print(f"🏠 Double 1X:  {resultado['1X']}")
    print(f"🚀 Double X2:  {resultado['X2']}")
    print("="*40, flush=True)
    
