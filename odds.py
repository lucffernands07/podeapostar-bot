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

def capturar_todas_as_odds(id_jogo):
    driver = configurar_driver()
    # Dicionário de retorno padrão
    res = {
        "GOLS_15": "N/A", 
        "GOLS_25": "N/A", 
        "GOLS_M45": "N/A", 
        "BTTS": "N/A", 
        "1X": "N/A", 
        "X2": "N/A"
    }

    try:
        # 1. ACESSA O RESUMO PARA PEGAR A URL REAL DAS ODDS
        url_resumo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo"
        driver.get(url_resumo)
        time.sleep(5)

        try:
            # Localiza o link da aba ODDS dinamicamente
            elemento_aba = driver.find_element(By.XPATH, "//a[contains(@href, '/odds/')]")
            link_odds_base = elemento_aba.get_attribute('href')
            print(f"    🔗 [DEBUG] URL Base de Odds encontrada: {link_odds_base}")
        except:
            print(f"    ⚠️ Aba ODDS não encontrada para o jogo {id_jogo}")
            return res

        # 2. MERCADO DE GOLS (Over/Under)
        # Substituímos a parte final da URL para ir direto ao mercado de gols
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(5)
            
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha in linhas:
                txt = linha.text
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                if len(spans) < 2: continue

                # Lógica para Gols 1.5
                if res["GOLS_15"] == "N/A" and "1.5" in txt:
                    for s in spans:
                        if "." in s and s != "1.5":
                            res["GOLS_15"] = s
                            break
                
                # Lógica para Gols 2.5
                elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                    for s in spans:
                        if "." in s and s != "2.5":
                            res["GOLS_25"] = s
                            break

                # Lógica para Gols 4.5 (Menos)
                elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                    decimais = [s for s in spans if "." in s and s != "4.5"]
                    if len(decimais) >= 2:
                        res["GOLS_M45"] = decimais[1] # Pega a odd do "Menos"
                        break
        except Exception as e:
            print(f"    ⚠️ Erro ao processar Gols: {e}")

        # 3. MERCADO AMBAS MARCAM (BTTS)
        try:
            url_btts = link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/")
            driver.get(url_btts)
            time.sleep(5)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if odds_b:
                res["BTTS"] = odds_b[0] # Odd do "Sim"
        except:
            pass

        # 4. MERCADO DUPLA CHANCE
        try:
            url_dc = link_odds_base.replace("/odds/", "/odds/double-chance/tempo-regulamentar/")
            driver.get(url_dc)
            time.sleep(5)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0]
                res["X2"] = odds_d[2]
        except:
            pass

    except Exception as e:
        print(f"    ❌ Erro crítico no odds.py para o ID {id_jogo}: {e}")
    
    finally:
        driver.quit()
    
    return res
