import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_todas_as_odds(driver, id_jogo):
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M45": "N/A", 
        "BTTS": "N/A", "1X": "N/A", "X2": "N/A"
    }

    driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        time.sleep(3)
        try:
            elemento_aba = driver.find_element(By.XPATH, "//a[contains(@href, '/odds/')]")
            link_odds_base = elemento_aba.get_attribute('href')
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return res

        # 1. MERCADO DE GOLS
        url_gols = link_odds_base.replace("/odds/", "/odds/acima-abaixo/tempo-regulamentar/")
        driver.get(url_gols)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
            time.sleep(3)
            
            linhas = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha in linhas:
                txt = linha.text
                spans = [s.text for s in linha.find_elements(By.TAG_NAME, "span") if s.text]
                if len(spans) < 2: continue

                # BUSCA 1.5
                if res["GOLS_15"] == "N/A" and "1.5" in txt:
                    for s in spans:
                        if "." in s and s != "1.5":
                            res["GOLS_15"] = s
                            break
                
                # BUSCA 2.5
                elif res["GOLS_15"] != "N/A" and res["GOLS_25"] == "N/A" and "2.5" in txt:
                    for s in spans:
                        if "." in s and s != "2.5":
                            res["GOLS_25"] = s
                            break

                # BUSCA 4.5 (COM A LÓGICA DA DIREITA)
                elif res["GOLS_25"] != "N/A" and res["GOLS_M45"] == "N/A" and "4.5" in txt:
                    # Filtramos a lista: removemos o "4.5" (título) e garantimos que sobraram as odds
                    odds_da_linha = []
                    for s in spans:
                        s_limpo = s.replace(',', '.').strip()
                        if "." in s_limpo:
                            try:
                                # Se o valor for 4.5, ignoramos pois é o título do mercado
                                if float(s_limpo) != 4.5:
                                    odds_da_linha.append(s)
                            except ValueError:
                                continue
                    
                    # No Flashscore: [0] é Acima (esquerda), [1] é Abaixo (direita)
                    # Como queremos o Menos de 4.5, pegamos sempre o índice 1
                    if len(odds_da_linha) >= 2:
                        res["GOLS_M45"] = odds_da_linha[1]
                        break
        except: pass

        # 2. BTTS
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/ambos-marcam/tempo-regulamentar/"))
            time.sleep(3)
            linha_b = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_b = [s.text for s in linha_b.find_elements(By.TAG_NAME, "span") if "." in s.text or "," in s.text]
            if odds_b: res["BTTS"] = odds_b[0]
        except: pass

        # 3. DUPLA CHANCE
        try:
            driver.get(link_odds_base.replace("/odds/", "/odds/double-chance/tempo-regulamentar/"))
            time.sleep(3)
            linha_d = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
            odds_d = [s.text for s in linha_d.find_elements(By.TAG_NAME, "span") if "." in s.text or "," in s.text]
            if len(odds_d) >= 3:
                res["1X"] = odds_d[0]
                res["X2"] = odds_d[2]
        except: pass

    except Exception as e:
        print(f"    ❌ Erro no odds.py: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return res
            
