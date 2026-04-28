import os
import time
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        return int(output.split()[2].split('.')[0])
    except: return None

def capturar_link_betano_pelo_titulo(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        print(f"🚀 [ROBÔ] Acessando jogo...")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 20)
        
        # 1. Espera o título das Odds aparecer (O seu seletor)
        print("🔍 [ROBÔ] Localizando seção de Odds...")
        titulo_odds = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "section__prematchOdds")))
        
        # 2. Rola até o título das odds para garantir o carregamento
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", titulo_odds)
        time.sleep(3)
        
        # 3. Busca o botão da Betano logo abaixo desse título
        # O seletor abaixo busca qualquer elemento com a imagem da Betano dentro da área de odds
        xpath_betano = "//div[contains(@class, 'section__prematchOdds')]/ancestor::div[contains(@class, 'h2h')]//img[@alt='Betano']/ancestor::a"
        
        btn_betano = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_betano)))
        print("🖱️ [ROBÔ] Clicando no link da Betano...")
        driver.execute_script("arguments[0].click();", btn_betano)
        
        # 4. Captura o link
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print(f"✅ [SUCESSO] URL Final: {driver.current_url}")
            return driver.current_url
            
    except Exception as e:
        print(f"❌ [ERRO]: {e}")
        driver.save_screenshot("erro_seletor.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    capturar_link_betano_pelo_titulo(url)
