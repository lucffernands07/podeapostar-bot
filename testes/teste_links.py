import sys
import os
import time
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_chrome_version():
    """Detecta a versão principal do Chrome instalada no sistema."""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except Exception:
        return None

def capturar_link_betano_via_flashscore(url_h2h):
    print(f"🚀 [ROBÔ] Iniciando captura para: {url_h2h}")
    
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')

    # Detecta versão para evitar erro de compatibilidade (v147 vs v148)
    main_version = get_chrome_version()
    print(f"🔍 [ROBÔ] Versão do Chrome detectada: {main_version}")

    try:
        driver = uc.Chrome(options=options, version_main=main_version)
        driver.get(url_h2h)
        
        wait = WebDriverWait(driver, 20)
        
        # Seletor baseado no seu print: foca no span da odd dentro do bloco da Betano
        # XPath procura o link (<a>) que contém a imagem da Betano e o valor da odd
        xpath_betano = "//div[contains(@class, 'wcl-bettingProvider')]//a[.//img[@alt='Betano']]"
        
        print("⏳ [ROBÔ] Aguardando elemento da Betano...")
        btn_betano = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_betano)))
        
        # Scroll até o elemento para garantir o clique
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_betano)
        time.sleep(2)
        
        print("🖱️ [ROBÔ] Clicando na Odd da Betano...")
        btn_betano.click()
        
        # Espera abrir a nova aba da Betano
        time.sleep(5)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        url_final = driver.current_url
        print(f"✅ [SUCESSO] URL capturada: {url_final}")
        
        return url_final

    except Exception as e:
        print(f"⚠️ [ERRO] Falha na captura: {str(e)}")
        # Tira print do erro para debug no GitHub Actions
        if 'driver' in locals():
            driver.save_screenshot("erro_selenium.png")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    # URL de exemplo (Substitua pela do Cruzeiro x Boca real do Flashscore)
    # Exemplo: https://www.flashscore.com.br/jogo/ELH8S7O0/#/resumo-de-jogo/h2h/overall
    url_teste = "https://www.flashscore.com.br/jogo/ELH8S7O0/#/resumo-de-jogo/h2h/overall"
    
    resultado = capturar_link_betano_via_flashscore(url_teste)
    
    print("\n" + "="*50)
    print(f"RESULTADO FINAL: {resultado}")
    print("="*50)
        
