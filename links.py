import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def capturar_link_direto(driver, time_casa, time_fora):
    # Link de busca padrão (fallback) caso tudo falhe
    link_busca_simples = f"https://www.betano.bet.br/search/?q={time_casa.replace(' ', '+')}+x+{time_fora.replace(' ', '+')}"
    
    try:
        print(f"🔍 Buscando na Betano: {time_casa} x {time_fora}")
        driver.get("https://www.betano.bet.br/")
        wait = WebDriverWait(driver, 10)

        # 1. Clicar na Lupa (Ela está dentro de um Shadow DOM)
        # Usamos JS para clicar porque o Selenium não "enxerga" dentro do kaizen-header direto
        script_lupa = "return document.querySelector('kaizen-header').shadowRoot.querySelector('button[data-qa=\"search-icon\"]') || document.querySelector('button[class*=\"search\"]')"
        btn_lupa = driver.execute_script(script_lupa)
        if btn_lupa:
            driver.execute_script("arguments[0].click();", btn_lupa)
        else:
            # Se não achar a lupa, tenta ir direto pela URL de busca para não perder tempo
            return link_busca_simples

        # 2. Clicar e digitar no campo de busca
        time.sleep(1)
        campo_busca = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-qa='input_search_modal']")))
        campo_busca.clear()
        campo_busca.send_keys(f"{time_casa} {time_fora}")
        time.sleep(2) # Espera carregar os resultados

        # 3. Clicar no primeiro resultado
        # O seletor abaixo busca a div que você mandou: search-result__info__name
        primeiro_resultado = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-result__info__name")))
        driver.execute_script("arguments[0].click();", primeiro_resultado)
        
        # 4. Copiar o link final
        time.sleep(2)
        link_final = driver.current_url
        
        if "odds/" in link_final:
            print(f"✅ Link encontrado: {link_final}")
            return link_final
        
        return link_busca_simples

    except Exception as e:
        print(f"⚠️ Falha ao buscar link real para {time_casa}: Usei link de busca padrão.")
        return link_busca_simples
        
