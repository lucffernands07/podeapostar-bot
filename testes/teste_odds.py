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

    driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        wait = WebDriverWait(driver, 12)
        try:
            elemento_aba = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/odds/')]")))
            link_odds_base = elemento_aba.get_attribute('href')
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return res

        # --- 1. MERCADOS DE LINHA ÚNICA (AJUSTADO PARA PEGAR A SEGUNDA LINHA) ---
        config_simples = [
            {"chave": "VITORIA_CASA", "path": "/odds/1x2-odds/tempo-regulamentar/", "col": 0},
            {"chave": "BTTS", "path": "/odds/ambos-marcam/tempo-regulamentar/", "col": 0},
            {"chave": "1X", "path": "/odds/double-chance/tempo-regulamentar/", "col": 0},
            {"chave": "X2", "path": "/odds/double-chance/tempo-regulamentar/", "col": 2}
        ]

        for item in config_simples:
            try:
                driver.get(link_odds_base.replace("/odds/", item["path"]))
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
                time.sleep(1.5)
                
                # BUSCA TODAS AS LINHAS DA TABELA
                linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
                
                # FORÇAMOS A SEGUNDA LINHA (Índice 1 - Betano conforme o print)
                if len(linhas) >= 2:
                    odds_tags = linhas[1].find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                    if len(odds_tags) > item["col"]:
                        valor_odd = odds_tags[item["col"]].text.replace('↑', '').replace('↓', '').strip()
                        res[item["chave"]] = valor_odd
            except: continue

        # --- 2. MERCADOS DE GOLS (MANTENDO A LÓGICA QUE JÁ ESTÁ FUNCIONANDO) ---
        driver.get(link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/"))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(2)
            
            alvos_gols = {
                "GOLS_15": {"valor": "1.5", "col": 0},
                "GOLS_25": {"valor": "2.5", "col": 0},
                "GOLS_M45": {"valor": "4.5", "col": 1}
            }

            for chave, config in alvos_gols.items():
                valor = config["valor"]
                col_idx = config["col"]
                
                xpath_linha = f"//div[contains(@class, 'ui-table__row')][.//span[@data-testid='wcl-oddsValue' and text()='{valor}']]"
                linhas_gols = driver.find_elements(By.XPATH, xpath_linha)

                if len(linhas_gols) >= 2:
                    segunda_linha_mercado = linhas_gols[1] # Pega a segunda linha de cada bloco de gol
                    odds_gols = segunda_linha_mercado.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                    if len(odds_gols) > col_idx:
                        res[chave] = odds_gols[col_idx].text.replace('↑', '').replace('↓', '').strip()
        except: pass

    except Exception as e:
        print(f"    ❌ Erro no odds.py: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return res
    
