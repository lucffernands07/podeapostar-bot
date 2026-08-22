import time
import unicodedata
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def _normalizar_texto(texto):
    """Remove acentos e deixa o texto minúsculo para facilitar o match."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def _encontrar_id_por_nomes(driver, t1_procurado, t2_procurado):
    """Varre a página de calendário atual do Flashscore para achar o ID correto do jogo pelos nomes com alta tolerância."""
    try:
        t1_limpo = _normalizar_texto(t1_procurado)
        t2_limpo = _normalizar_texto(t2_procurado)
        
        # Pega a primeira palavra ou pedaço principal caso haja divergência de sufixos (ex: "São Paulo" vs "Sao Paulo FC")
        t1_chave = t1_limpo.split()[0] if t1_limpo else ""
        t2_chave = t2_limpo.split()[0] if t2_limpo else ""

        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        for el in elementos:
            try:
                times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                if len(times) >= 2:
                    t1_atual = _normalizar_texto(times[0].text)
                    t2_atual = _normalizar_texto(times[1].text)
                    
                    # Critério flexível: contém o nome completo OU contém a palavra-chave principal de ambos os times
                    match_t1 = (t1_limpo in t1_atual or t1_atual in t1_limpo or (t1_chave and t1_chave in t1_atual))
                    match_t2 = (t2_limpo in t2_atual or t2_atual in t2_limpo or (t2_chave and t2_chave in t2_atual))
                    
                    if match_t1 and match_t2:
                        link_el = el.find_element(By.CSS_SELECTOR, "a.icon--preview, a.eventRowLink")
                        href = link_el.get_attribute('href')
                        if "mid=" in href:
                            return href.split("mid=")[-1].split("&")[0]
                        else:
                            id_el = link_el.get_attribute('id')
                            if id_el:
                                return id_el.split('_')[-1]
            except:
                continue
    except Exception as e:
        print(f"    ⚠️ Erro ao buscar ID no Flashscore por nomes: {e}")
    return None

def capturar_todas_as_odds(driver, id_ou_t1, t2=None):
    """
    Pode receber:
      - capturar_todas_as_odds(driver, id_jogo) -> Se já tiver o ID do Flashscore.
      - capturar_todas_as_odds(driver, t1, t2) -> Se precisar fazer o match por nome do time.
    """
    janela_principal = driver.current_window_handle
    
    # Dicionário completo padrão
    res = {
        "GOLS_15": "N/A", "GOLS_25": "N/A", "GOLS_M35": "N/A", "GOLS_M45": "N/A", 
        "BTTS_SIM": "N/A", "BTTS_NAO": "N/A",
        "1X": "N/A", "X2": "N/A",
        "VITORIA_CASA": "N/A", "VITORIA_FORA": "N/A"
    }

    try:
        # Se t2 foi informado, significa que o segundo parâmetro é o time da casa e o terceiro é o visitante
        if t2 is not None:
            t1_procurado = id_ou_t1
            t2_procurado = t2
            
            # Abre a página de jogos do dia no Flashscore para localizar o ID correspondente
            driver.execute_script("window.open('https://www.flashscore.com.br/futebol/hoje/', '_blank');")
            time.sleep(1.0)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(1.5)
            
            id_jogo = _encontrar_id_por_nomes(driver, t1_procurado, t2_procurado)
            
            # Fecha a aba de busca e retorna para a janela principal
            driver.close()
            driver.switch_to.window(janela_principal)
            
            if not id_jogo:
                print(f"    ⚠️ Matchmaking do Flashscore não encontrou o jogo: {t1_procurado} x {t2_procurado}")
                return res
        else:
            id_jogo = id_ou_t1

        # Abre a aba de resumo para pegar o link base de odds do jogo correto
        driver.execute_script(f"window.open('https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo', '_blank');")
        time.sleep(1.0)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        else:
            return res

        try:
            elemento_aba = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/odds/')]"))
            )
            link_odds_base = elemento_aba.get_attribute('href')
        except:
            driver.close()
            driver.switch_to.window(janela_principal)
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
            
            linhas_b = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
            for linha_b in linhas_b:
                odds_b = linha_b.find_elements(By.CSS_SELECTOR, "a.oddsCell__odd")
                if len(odds_b) >= 2:
                    val_sim = odds_b[0].text.replace('↑', '').replace('↓', '').strip()
                    val_nao = odds_b[1].text.replace('↑', '').replace('↓', '').strip()
                    
                    if val_sim and val_sim != "-":
                        res["BTTS_SIM"] = val_sim
                        res["BTTS_NAO"] = val_nao
                        break
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
        try:
            if len(driver.window_handles) > 1:
                driver.close()
        except:
            pass
        try:
            driver.switch_to.window(janela_principal)
        except:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
    
    return res
    
