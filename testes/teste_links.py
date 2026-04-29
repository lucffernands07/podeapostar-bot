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
        return int(re.search(r'Google Chrome (\d+)', output).group(1))
    except: return None

def capturar_com_redirecionamento_lento(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3500")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        print(f"🚀 [ROBÔ] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)
        
        # 1. Localiza a Betano pelo link (mais estável que imagem no headless)
        print("🔍 [ROBÔ] Localizando linha da Betano...")
        xpath_betano = "//a[contains(@href, 'betano')]"
        linha_betano = wait.until(EC.presence_of_element_located((By.XPATH, xpath_betano)))
        
        # 2. Pega a segunda odd daquela linha
        xpath_segunda_odd = "./following::span[@data-testid='wcl-oddsValue'][2]"
        segunda_odd_el = linha_betano.find_element(By.XPATH, xpath_segunda_odd)
        
        print(f"🎯 [ROBÔ] Clicando na odd: {segunda_odd_el.text}")
        driver.execute_script("arguments[0].click();", segunda_odd_el)

        # 3. Monitoramento da Nova Aba
        print("⏳ [ROBÔ] Aguardando a nova aba abrir...")
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # 4. LOOP DE REDIRECIONAMENTO (A mágica acontece aqui)
        print("🔄 [ROBÔ] Detectado link de ponte. Monitorando redirecionamento para Betano...")
        
        url_final = ""
        tentativas = 0
        while tentativas < 15: # Tenta por até 15 segundos
            url_atual = driver.current_url
            print(f"📡 [DEBUG] URL atual: {url_atual[:50]}...")
            
            if "betano.com" in url_atual and "flashscore" not in url_atual:
                url_final = url_atual
                print("✅ [OK] Redirecionamento concluído!")
                break
            
            time.sleep(1) # Espera 1 segundo e checa de novo
            tentativas += 1
        
        if not url_final:
            url_final = driver.current_url
            print("⚠️ [AVISO] Tempo esgotado, capturando URL atual mesmo assim.")

        print(f"\n==================================================")
        print(f"RESULTADO FINAL: {url_final}")
        print(f"==================================================")

    except Exception as e:
        print(f"❌ Erro: {e}")
        driver.save_screenshot("erro_redirecionamento.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    capturar_com_redirecionamento_lento(url)
        
