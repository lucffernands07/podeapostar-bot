import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_url_betano(driver):
    try:
        # 1. Espera os botões de odds aparecerem (aumentei para 10s por segurança)
        wait = WebDriverWait(driver, 10)
        
        # 2. Localiza a linha que contém a palavra 'Betano' e pega o botão de Odds dela
        # Isso ignora se a Betano é a 1ª, 2ª ou 3ª. Ele busca pelo nome.
        try:
            xpath_botao = "//img[contains(@alt, 'Betano')]/ancestor::tr//button[@data-testid='wcl-oddsCell']"
            botao_alvo = wait.until(EC.presence_of_element_located((By.XPATH, xpath_botao)))
            
            # Scroll até o botão para garantir que o Selenium o veja
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
            time.sleep(1) 
        except:
            # Fallback caso a estrutura seja diferente: tenta o 4º botão como você fazia
            botoes = driver.find_elements(By.XPATH, "//button[@data-testid='wcl-oddsCell']")
            if len(botoes) >= 4:
                botao_alvo = botoes[3]
            else:
                return None

        # 3. Clique forçado via JS
        driver.execute_script("arguments[0].click();", botao_alvo)
        
        # 4. Gerencia a troca de abas
        aba_original = driver.current_window_handle
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # 5. Captura a URL real (Aumentamos o tempo de espera pelo redirecionamento)
        url_final = ""
        for _ in range(20): 
            url_atual = driver.current_url
            if "match-odds" in url_atual or "betano" in url_atual:
                url_final = url_atual.split('?')[0]
                if not url_final.endswith('/'):
                    url_final += '/'
                break
            time.sleep(1)
        
        # 6. Fecha e volta
        driver.close()
        driver.switch_to.window(aba_original)
        return url_final if "betano" in url_final else None

    except Exception as e:
        print(f"⚠️ Erro ao capturar link real: {e}")
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[0])
        return None
        
