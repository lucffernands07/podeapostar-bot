import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_link_direto(driver, time_casa, time_fora):
    # Link de busca reserva caso o processo falhe
    link_fallback = f"https://www.betano.bet.br/search/?q={time_casa.replace(' ', '+')}"
    
    try:
        print(f"🔍 Buscando link real: {time_casa} x {time_fora}")
        driver.get("https://www.betano.bet.br/")
        wait = WebDriverWait(driver, 12)

        # 1. Clicar na Lupa (Fura o Shadow DOM do kaizen-header)
        # Usamos JavaScript porque o Selenium puro não entra no Shadow Root facilmente
        script_lupa = """
            return document.querySelector('kaizen-header')
            .shadowRoot.querySelector('button[data-qa="search-icon"]')
        """
        try:
            btn_lupa = driver.execute_script(script_lupa)
            driver.execute_script("arguments[0].click();", btn_lupa)
        except:
            # Se o kaizen-header mudar, tenta um seletor comum de busca
            btn_reserva = driver.find_element(By.CSS_SELECTOR, "button[class*='search']")
            btn_reserva.click()

        # 2. Clicar no campo e digitar (data-qa="input_search_modal")
        campo_busca = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-qa='input_search_modal']")))
        campo_busca.clear()
        campo_busca.send_keys(f"{time_casa} {time_fora}")
        time.sleep(3) # Tempo para os resultados aparecerem

        # 3. Clicar no primeiro resultado (.search-result__info__name)
        # O seletor abaixo bate com o HTML que você mandou
        primeiro_item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-result__info__name")))
        driver.execute_script("arguments[0].click();", primeiro_item)
        
        # 4. Capturar a nova URL
        time.sleep(2)
        url_final = driver.current_url
        
        if "odds/" in url_final:
            print(f"✅ Sucesso: {url_final}")
            return url_final
        else:
            return link_fallback

    except Exception as e:
        print(f"⚠️ Betano: Não foi possível capturar link real para {time_casa}. Usando busca.")
        return link_fallback
        
