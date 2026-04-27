import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_todas_as_odds(driver, id_jogo):
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A",
        "VITORIA_CASA": "N/A"
    }

    # Abre a aba de resumo para pegar o link base
    driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        time.sleep(3)
        try:
            elemento_aba = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/odds/')]"))
            )
            link_odds_base = elemento_aba.get_attribute('href')
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return res

        # --- 1. VITÓRIA SECA (1X2) ---
        # Conforme seu print, é a aba inicial '1X2'
        url_1x2 = link_odds_base.replace("/odds/", "/odds/1x2-odds/tempo-regulamentar/")
        driver.get(url_1x2)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(2)
            # Pega a primeira linha após o título 'CASA DE APOSTAS'
            linha_1x2 = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_1x2 = linha_1x2.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if odds_1x2:
                # O primeiro decimal da coluna '1'
                res["VITORIA_CASA"] = odds_1x2[0].text.strip()
        except: pass

        # --- 2. MERCADO DE GOLS (ACIMA/ABAIXO) ---
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        driver.get(url_gols)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(2)
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha in linhas:
                txt = linha.text
                odds_celulas = linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                if not odds_celulas: continue

                if "1.5" in txt and res["GOLS_15"] == "N/A":
                    res["GOLS_15"] = odds_celulas[0].text.strip()
                elif "2.5" in txt and res["GOLS_25"] == "N/A":
                    res["GOLS_25"] = odds_celulas[0].text.strip()
                elif "4.5" in txt and res["GOLS_M45"] == "N/A":
                    if len(odds_celulas) >= 2:
                        res["GOLS_M45"] = odds_celulas[1].text.strip()
        except: pass

        # --- 3. AMBOS MARCAM (BTTS) ---
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/"))
            time.sleep(2)
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = linha_b.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if odds_b: res["BTTS"] = odds_b[0].text.strip()
        except: pass

        # --- 4. DUPLA CHANCE ---
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/double-chance/tempo-regulamentar/"))
            time.sleep(2)
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = linha_d.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0].text.strip()
                res["X2"] = odds_d[2].text.strip()
        except: pass

    except Exception as e:
        print(f"    ❌ Erro no odds.py: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return res
            
