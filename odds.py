import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_todas_as_odds(driver, id_jogo):
    # Dicionário de retorno padrão
    res = {
        "GOLS_15": "N/A", 
        "GOLS_25": "N/A", 
        "GOLS_M45": "N/A", 
        "BTTS": "N/A", 
        "1X": "N/A", 
        "X2": "N/A"
    }

    # ABRE UMA NOVA ABA PARA NÃO MEXER NA PÁGINA PRINCIPAL DO MAIN
    driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        # 1. PEGA A URL REAL DAS ODDS (Ajustado para 3s para ser mais rápido)
        time.sleep(3)
        try:
            elemento_aba = driver.find_element(By.XPATH, "//a[contains(@href, '/odds/')]")
            link_odds_base = elemento_aba.get_attribute('href')
        except:
            print(f"    ⚠️ Aba ODDS não encontrada para o jogo {id_jogo}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return res

        # 2. MERCADO DE GOLS
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(2) # Sleep reduzido
            
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha in linhas:
                txt = linha.text
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                if len(spans) < 2: continue

                if res["GOLS_15"] == "N/A" and "1.5" in txt:
                    for s in spans:
                        if "." in s and s != "1.5": res["GOLS_15"] = s; break
                
                elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                    for s in spans:
                        if "." in s and s != "2.5": res["GOLS_25"] = s; break

                elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                    decimais = [s for s in spans if "." in s and s != "4.5"]
                    if len(decimais) >= 2: res["GOLS_M45"] = decimais[1]; break
        except: pass

        # 3. MERCADO AMBAS MARCAM (BTTS)
        try:
            url_btts = link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/")
            driver.get(url_btts)
            time.sleep(2)
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if odds_b: res["BTTS"] = odds_b[0]
        except: pass

        # 4. MERCADO DUPLA CHANCE
        try:
            url_dc = link_odds_base.replace("/odds/", "/odds/double-chance/tempo-regulamentar/")
            driver.get(url_dc)
            time.sleep(2)
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text]
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0]
                res["X2"] = odds_d[2]
        except: pass

    except Exception as e:
        print(f"    ❌ Erro no odds.py: {e}")
    
    finally:
        # FECHA A ABA DE ODDS E VOLTA PARA A PRINCIPAL
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return res
                            
