import time
import re
import links
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    """
    RASPAGEM 1: Navega direto pelas URLs /h2h/casa/ e /h2h/fora/
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
    
    aba_principal = driver.window_handles[0]
    
    # 🔗 Normaliza e estrutura as URLs de Casa e Fora
    url_limpa = url_jogo.rstrip("/")
    if "/h2h" in url_limpa:
        url_base_h2h = url_limpa.split("/h2h")[0] + "/h2h"
    else:
        url_base_h2h = url_limpa + "/h2h"

    url_casa = f"{url_base_h2h}/casa/"
    url_fora = f"{url_base_h2h}/fora/"

    stats["url_h2h_base"] = url_base_h2h

    # Abre a aba do jogo
    driver.execute_script(f"window.open('{url_casa}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        # --- CAPTURA DO LINK DA BETANO ---
        try:
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            stats["link_betano"] = links.extrair_url_betano(driver)
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano inicial: {e_link}")

        # -----------------------------------------------------------------
        # 1. RASPAGEM: MANDANTE JOGANDO EM CASA (/h2h/casa/)
        # -----------------------------------------------------------------
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if secoes:
                linhas_casa = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
                for i, linha in enumerate(linhas_casa):
                    n_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    
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
        # 2. RASPAGEM: VISITANTE JOGANDO FORA (/h2h/fora/)
        # -----------------------------------------------------------------
        try:
            driver.get(url_fora)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if secoes:
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

    except Exception as e:
        print(f"      ⚠️ Erro Geral na Raspagem 1: {e}")
    
    finally:
        # Garante o fechamento da aba secundária e o retorno seguro
        if len(driver.window_handles) > 1:
            try:
                driver.close()
                driver.switch_to.window(aba_principal)
            except Exception:
                pass

    return stats
                                                                      
