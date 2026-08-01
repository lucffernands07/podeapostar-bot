import time
import re
import links
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    """
    RASPAGEM 1: Acessa o H2H, clica nos filtros CASA e FORA,
    e computa os últimos 5 jogos do mandante em casa e visitante fora.
    """
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_btts": 0, 
        "fora_vitorias_recente": 0, "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", 
        "h2h_geral_res_1": "", "h2h_geral_res_2": "", "h2h_geral_res_3": "", "h2h_geral_res_4": "", "h2h_geral_res_5": "",
        "t1_placar_1": None, "t2_placar_1": None,     
        "h2h_placar_1": None, "h2h_placar_2": None,   
        "pular_gols": False,
        "url_h2h_base": None,
        "historico_chutes": {}, 
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {}
    }
    
    # Abre o confronto em uma nova aba
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # Clica na aba H2H do Flashscore
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(1.5)
        
        # Guarda a URL base do H2H
        stats["url_h2h_base"] = driver.current_url

        # --- CAPTURA DO LINK DA BETANO ---
        try:
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            stats["link_betano"] = links.extrair_url_betano(driver)
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano inicial: {e_link}")
        
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)

        # -----------------------------------------------------------------
        # 1. FILTRO: MANDANTE JOGANDO EM CASA (Últimos 5 jogos)
        # -----------------------------------------------------------------
        try:
            btn_casa = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CASA')]")))
            driver.execute_script("arguments[0].click();", btn_casa)
            time.sleep(1.2)

            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if secoes:
                linhas_casa = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
                for i, linha in enumerate(linhas_casa):
                    n_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    
                    # Trata placar isolando números para evitar colagem de texto (ex: '2-0')
                    nums = re.findall(r'\d+', res_el.text)
                    if len(nums) < 2: continue
                    g1, g2 = int(nums[0]), int(nums[1])
                    placar_str = f"{g1}-{g2}"

                    if i == 0: stats["t1_placar_1"] = placar_str

                    total = g1 + g2
                    if i == 0: stats["ultimo_gols_casa"] = total
                    if total > 1.5: stats["casa_15"] += 1
                    if total > 2.5: stats["casa_25"] += 1
                    if total <= 3: stats["casa_35_under"] += 1
                    if total <= 4: stats["casa_45_under"] += 1 
                    if g1 > 0 and g2 > 0: stats["casa_btts"] += 1
                    
                    res_atual = "E"
                    if (t1.lower() in n_casa.lower() and g1 > g2) or (t1.lower() in n_fora.lower() and g2 > g1):
                        res_atual = "V"
                        stats["casa_vitorias_recente"] += 1
                    elif (t1.lower() in n_casa.lower() and g1 < g2) or (t1.lower() in n_fora.lower() and g2 < g1):
                        res_atual = "D"
                    
                    if i == 0: stats["t1_resultado_1"] = res_atual
        except Exception as e_casa:
            print(f"      ⚠️ Erro ao raspar jogos do Casa (em casa): {e_casa}")

        # -----------------------------------------------------------------
        # 2. FILTRO: VISITANTE JOGANDO FORA (Últimos 5 jogos)
        # -----------------------------------------------------------------
        try:
            btn_fora = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'FORA')]")))
            driver.execute_script("arguments[0].click();", btn_fora)
            time.sleep(1.2)

            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if secoes:
                # Na view do filtro 'FORA', a 1ª tabela em exibição corresponde ao Visitante fora
                linhas_fora = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
                for i, linha in enumerate(linhas_fora):
                    n_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    
                    nums = re.findall(r'\d+', res_el.text)
                    if len(nums) < 2: continue
                    g1, g2 = int(nums[0]), int(nums[1])
                    placar_str = f"{g1}-{g2}"

                    if i == 0: stats["t2_placar_1"] = placar_str

                    total = g1 + g2
                    if i == 0: stats["ultimo_gols_fora"] = total
                    if total > 1.5: stats["fora_15"] += 1
                    if total > 2.5: stats["fora_25"] += 1
                    if total <= 3: stats["fora_35_under"] += 1
                    if total <= 4: stats["fora_45_under"] += 1 
                    if g1 > 0 and g2 > 0: stats["fora_btts"] += 1
                    
                    res_atual = "E"
                    if (t2.lower() in n_casa.lower() and g1 > g2) or (t2.lower() in n_fora.lower() and g2 > g1):
                        res_atual = "V"
                        stats["fora_vitorias_recente"] += 1
                    elif (t2.lower() in n_casa.lower() and g1 < g2) or (t2.lower() in n_fora.lower() and g2 < g1):
                        res_atual = "D"
                    
                    if i == 0: stats["t2_resultado_1"] = res_atual
        except Exception as e_fora:
            print(f"      ⚠️ Erro ao raspar jogos do Fora (fora): {e_fora}")

        # -----------------------------------------------------------------
        # 3. RASPAGEM: CONFRONTOS DIRETO H2H (Histórico Geral)
        # -----------------------------------------------------------------
        try:
            # Reseta para TOTAL para ler o H2H histórico completo entre os dois
            btn_total = driver.find_element(By.XPATH, "//button[contains(text(), 'TOTAL')]")
            driver.execute_script("arguments[0].click();", btn_total)
            time.sleep(1)

            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if len(secoes) >= 3:
                secao_h2h = secoes[2]
                try:
                    seletor_btn = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao_h2h.find_element(By.CSS_SELECTOR, seletor_btn)
                    driver.execute_script("arguments[0].click();", botao_mais)
                    WebDriverWait(secao_h2h, 4).until(lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6)
                except:
                    pass

                linhas_h2h = secao_h2h.find_elements(By.CSS_SELECTOR, ".h2h__row")[:6]
                for i, linha in enumerate(linhas_h2h):
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    
                    nums = re.findall(r'\d+', res_el.text)
                    if len(nums) < 2: continue
                    g1, g2 = int(nums[0]), int(nums[1])

                    if i == 0: stats["h2h_placar_1"] = f"{g1}-{g2}"
                    if i == 1: stats["h2h_placar_2"] = f"{g1}-{g2}"

                    if i < 5:
                        res_geral = "EMPATE"
                        if g1 > g2:
                            if t1.lower() in n_casa_h2h.lower(): res_geral = "CASA"
                            elif t2.lower() in n_casa_h2h.lower(): res_geral = "FORA"
                        elif g1 < g2:
                            if t1.lower() in n_fora_h2h.lower(): res_geral = "CASA"
                            elif t2.lower() in n_fora_h2h.lower(): res_geral = "FORA"
                        
                        stats[f"h2h_geral_res_{i+1}"] = res_geral

                    stats["h2h_jogos"] += 1
                    
                    if g1 == g2:
                        res_h2h = "E"
                        stats["h2h_empates"] += 1
                    else:
                        t1_ganhou = (t1.lower() in n_casa_h2h.lower() and g1 > g2) or (t1.lower() in n_fora_h2h.lower() and g2 > g1)
                        if t1_ganhou:
                            res_h2h = "V"
                            stats["h2h_vitorias_t1"] += 1
                        else:
                            res_h2h = "D"
                            stats["h2h_vitorias_t2"] += 1
                    
                    if stats["h2h_res_1"] == "": stats["h2h_res_1"] = res_h2h
                    elif stats["h2h_res_2"] == "": stats["h2h_res_2"] = res_h2h
        except Exception as e_h2h:
            print(f"      ⚠️ Erro ao raspar H2H Histórico: {e_h2h}")

    except Exception as e:
        print(f"      ⚠️ Erro Geral na Raspagem 1: {e}")
        
    return stats
            
