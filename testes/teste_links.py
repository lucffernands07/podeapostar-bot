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

def capturar_segunda_odd_h2h(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3500")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        print(f"🚀 [ROBÔ] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 25)
        
        # 1. Localiza o Título "Odds" como âncora
        print("🔍 [ROBÔ] Localizando âncora 'Odds'...")
        xpath_titulo = "//div[contains(@class, 'section__prematchOdds')]"
        titulo_el = wait.until(EC.presence_of_element_located((By.XPATH, xpath_titulo)))
        
        # 2. Busca todos os spans de odds que seguem o título
        # O XPath abaixo pega o segundo span com data-testid='wcl-oddsValue' após o título
        xpath_segunda_odd = ".//following::span[@data-testid='wcl-oddsValue'][2]"
        
        print("🎯 [ROBÔ] Tentando clicar no SEGUNDO valor de odd...")
        segunda_odd_el = titulo_el.find_element(By.XPATH, xpath_segunda_odd)
        valor_detectado = segunda_odd_el.text
        print(f"💰 Valor da Odd no alvo: {valor_detectado}")

        # 3. Realiza o clique no elemento (ou no link pai dele)
        # Muitas vezes o clique precisa ser no <a> que envolve o span
        try:
            link_pai = segunda_odd_el.find_element(By.XPATH, "./ancestor::a")
            driver.execute_script("arguments[0].click();", link_pai)
        except:
            driver.execute_script("arguments[0].click();", segunda_odd_el)

        print("⏳ [ROBÔ] Aguardando carregamento da Betano...")
        
        # 4. Espera a nova aba abrir e captura a URL
        # A Betano pode demorar para processar o token de afiliado
        time.sleep(10) 

        if len(driver.window_handles) > 1:
            # Muda para a aba mais recente
            driver.switch_to.window(driver.window_handles[-1])
        
        url_final = driver.current_url
        print(f"✅ [SUCESSO] URL FINAL CAPTURADA: {url_final}")
        
        if "betano" not in url_final:
            print("⚠️ A URL capturada não parece ser da Betano. Verifique se o clique abriu a aba correta.")

    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        driver.save_screenshot("erro_segunda_odd.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    capturar_segunda_odd_h2h(url)
