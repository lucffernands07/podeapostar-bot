import os
import time
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except Exception:
        return None

def capturar_link_estilo_main(url_jogo):
    # Configuração de driver idêntica ao seu configurar_driver()
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3000") # Janela alta do seu main
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    main_version = get_chrome_version()
    driver = uc.Chrome(options=options, version_main=main_version)
    
    print(f"🚀 [TESTE] Abrindo Flashscore: {url_jogo}")
    
    try:
        # LÓGICA DO SEU MAIN: Abre em nova aba
        driver.get("about:blank") # Começa em branco
        driver.execute_script(f"window.open('{url_jogo}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        wait = WebDriverWait(driver, 15)

        # LÓGICA DO SEU MAIN: Clica no H2H para garantir carregamento
        print("🔍 [TESTE] Clicando na aba H2H...")
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(5) # O tempo que você usa no main

        # Scroll para garantir (igual ao seu main)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)

        # --- A PARTE QUE DESCOBRIMOS ---
        # Agora que as tabelas carregaram (como no seu main), buscamos a Betano logo abaixo
        print("⏳ [TESTE] Buscando link da Betano abaixo das tabelas...")
        
        # Seletor baseado na imagem que você mandou (imagem da betano ou valor da odd)
        xpath_betano = "//div[contains(@class, 'wcl-bettingProvider')]//a[.//img[@alt='Betano']]"
        
        btn_betano = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_betano)))
        
        print("🖱️ [TESTE] Clicando na Betano...")
        driver.execute_script("arguments[0].click();", btn_betano)
        
        # Espera o redirecionamento (Betano abrindo em uma 3ª aba)
        time.sleep(6)
        
        if len(driver.window_handles) > 2:
            driver.switch_to.window(driver.window_handles[-1])
            url_final = driver.current_url
            print(f"✅ [SUCESSO] URL Betano: {url_final}")
            return url_final
        else:
            # Se não abriu nova aba, tenta pegar a URL da aba atual (caso tenha aberto na mesma)
            url_final = driver.current_url
            print(f"ℹ️ [INFO] URL Atual: {url_final}")
            return url_final

    except Exception as e:
        print(f"❌ [ERRO] Falha no teste: {e}")
        driver.save_screenshot("erro_teste_main.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Link do jogo que você quer testar
    link_jogo = "https://www.flashscore.com.br/jogo/ELH8S7O0/#/resumo-de-jogo"
    capturar_link_estilo_main(link_jogo)
        
