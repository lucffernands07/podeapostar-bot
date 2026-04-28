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
        
        # 1. Localiza a linha da Betano especificamente
        # Isso evita pegar valores da Bet365 que aparecem antes no log
        print("🔍 [ROBÔ] Localizando linha da Betano...")
        xpath_linha_betano = "//div[contains(@class, 'wcl-bettingProvider')]//a[.//img[@alt='Betano']]"
        linha_betano = wait.until(EC.presence_of_element_located((By.XPATH, xpath_linha_betano)))
        
        # 2. Busca a SEGUNDA odd DENTRO da linha da Betano
        # O [2] aqui garante que pegamos o segundo valor daquela linha específica
        xpath_segunda_odd = ".//following::span[@data-testid='wcl-oddsValue'][2]"
        segunda_odd_el = linha_betano.find_element(By.XPATH, xpath_segunda_odd)
        
        print(f"🎯 [ROBÔ] Clicando na segunda odd (Valor: {segunda_odd_el.text})")

        # 3. Realiza o clique
        driver.execute_script("arguments[0].click();", segunda_odd_el)

        # 4. Espera inteligente pela nova aba e redirecionamento
        print("⏳ [ROBÔ] Aguardando redirecionamento para Betano...")
        
        # Espera abrir a segunda aba
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # ESPERA CRÍTICA: Aguarda a URL mudar de 'flashscore' para qualquer outra coisa (o destino final)
        # Isso resolve o problema de capturar a URL do flashscore por pressa
        wait.until(lambda d: "flashscore" not in d.current_url)
        
        # Dá um fôlego extra para os parâmetros de tracking da Betano carregarem
        time.sleep(3) 
        
        url_final = driver.current_url
        print(f"✅ [SUCESSO] URL FINAL: {url_final}")
        
    except Exception as e:
        print(f"❌ Erro na captura: {e}")
        driver.save_screenshot("erro_segunda_odd.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    capturar_segunda_odd_h2h(url)
    
