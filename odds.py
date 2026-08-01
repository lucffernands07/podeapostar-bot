import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_todas_as_odds(driver, id_jogo):
    # Dicionário completo incluindo BTTS_NAO e VITORIA_FORA
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M35": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "BTTS_NAO": "N/A",
        "1X": "N/A", "X2": "N/A",
        "VITORIA_CASA": "N/A", "VITORIA_FORA": "N/A"
    }

    # Abre a aba de resumo para pegar o link base
    driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        time.sleep(1.5)
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
        url_1x2 = link_odds_base.replace("/odds/", "/odds/1x2-odds/tempo-regulamentar/")
        driver.get(url_1x2)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(1.5)
            linha_1x2 = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_1x2 = linha_1x2.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if len(odds_1x2) >= 3:
                # [0] = Casa | [1] = Empate | [2] = Fora
                res["VITORIA_CASA"] = odds_1x2[0].text.replace('↑', '').replace('↓', '').strip()
                res["VITORIA_FORA"] = odds_1x2[2].text.replace('↑', '').replace('↓', '').strip()
        except: pass

        # --- 2. MERCADO DE GOLS (ACIMA/ABAIXO) ---
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        driver.get(url_gols)
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(1.5)
            
            mercados_alvo = {
                "1.5": {"chave": "GOLS_15", "col": 0},  # Acima
                "2.5": {"chave": "GOLS_25", "col": 0},  # Acima
                "3.5": {"chave": "GOLS_M35", "col": 1}, # Abaixo
                "4.5": {"chave": "GOLS_M45", "col": 1}  # Abaixo
            }

            for valor, config in mercados_alvo.items():
                xpath = f"//div[contains(@class, 'ui-table__row')][.//span[@data-testid='wcl-oddsValue' and text()='{valor}']]"
                linhas = driver.find_elements(By.XPATH, xpath)

                if len(linhas) >= 2:
                    segunda_linha = linhas[1]
                    odds_tags = segunda_linha.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                    if len(odds_tags) >= 2:
                        odd_raw = odds_tags[config["col"]].text
                        res[config["chave"]] = odd_raw.replace('↑', '').replace('↓', '').strip()
        except: pass

        # --- 3. AMBOS MARCAM (BTTS SIM / BTTS NÃO) ---
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/"))
            time.sleep(1.5)
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = linha_b.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if len(odds_b) >= 2:
                # [0] = Sim | [1] = Não
                res["BTTS"] = odds_b[0].text.replace('↑', '').replace('↓', '').strip()
                res["BTTS_NAO"] = odds_b[1].text.replace('↑', '').replace('↓', '').strip()
        except: pass

        # --- 4. DUPLA CHANCE ---
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/double-chance/tempo-regulamentar/"))
            time.sleep(1.5)
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = linha_d.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0].text.replace('↑', '').replace('↓', '').strip()
                res["X2"] = odds_d[2].text.replace('↑', '').replace('↓', '').strip()
        except: pass

    except Exception as e:
        print(f"    ❌ Erro no odds.py: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return res
            
