import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def capturar_todas_as_odds_teste(driver, id_jogo):
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A",
        "VITORIA_CASA": "N/A"
    }

    # Passo 1: Acessar resumo para pegar o link base
    url_resumo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo"
    print(f"--- PASSO 1: Acessando {url_resumo}")
    driver.get(url_resumo)

    try:
        # Pega o link base de odds (ex: .../odds/acima-abaixo/...)
        elemento_aba = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/odds/')]"))
        )
        link_odds_base = elemento_aba.get_attribute('href')
        print(f"Link base detectado: {link_odds_base}")

        # --- 2. MERCADO DE GOLS (ACIMA/ABAIXO) ---
        # Foco total aqui conforme seu pedido do segundo 1.5 e 2.5
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        print(f"\n--- PASSO 2: Indo para Gols: {url_gols}")
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(3)
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            
            # Dicionários para controlar qual ocorrência estamos pegando
            contadores = {"1.5": 0, "2.5": 0, "4.5": 0}

            for linha in linhas:
                txt = linha.text
                odds_celulas = linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                if not odds_celulas: continue

                # LÓGICA PARA 1.5 (SEGUNDA OCORRÊNCIA)
                if "1.5" in txt:
                    contadores["1.5"] += 1
                    if contadores["1.5"] == 2: # <--- Pega a segunda
                        res["GOLS_15"] = odds_celulas[0].text.strip()
                        print(f"✅ GOLS_15 (2ª linha): {res['GOLS_15']}")

                # LÓGICA PARA 2.5 (SEGUNDA OCORRÊNCIA)
                elif "2.5" in txt:
                    contadores["2.5"] += 1
                    if contadores["2.5"] == 2: # <--- Pega a segunda
                        res["GOLS_25"] = odds_celulas[0].text.strip()
                        print(f"✅ GOLS_25 (2ª linha): {res['GOLS_25']}")

                # LÓGICA PARA 4.5 (SEGUNDA OCORRÊNCIA - ABAIXO)
                elif "4.5" in txt:
                    contadores["4.5"] += 1
                    if contadores["4.5"] == 2: # <--- Pega a segunda
                        if len(odds_celulas) >= 2:
                            res["GOLS_M45"] = odds_celulas[1].text.strip() # [1] é o Abaixo
                            print(f"✅ GOLS_M45 (2ª linha Abaixo): {res['GOLS_M45']}")
        except Exception as e:
            print(f"Erro em Gols: {e}")

        # --- OS OUTROS MERCADOS CONTINUAM IGUAL ---
        # BTTS
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/"))
            time.sleep(2)
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            res["BTTS"] = linha_b.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")[0].text.strip()
            print(f"✅ BTTS: {res['BTTS']}")
        except: pass

    except Exception as e:
        print(f"❌ Erro Geral: {e}")
    
    return res

if __name__ == "__main__":
    driver = configurar_driver()
    # ID Botafogo x Remo conforme sua URL
    id_teste = "jXzWoWa5" 
    resultado = capturar_todas_as_odds_teste(driver, id_teste)
    print(f"\n--- RESULTADO FINAL DO TESTE ---\n{resultado}")
    driver.quit()
        
