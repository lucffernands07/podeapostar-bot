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

def executar_fluxo_final(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,4000")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        print("🔍 [PASSO 2] Localizando seção de Odds...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'section__prematchOdds')]")))
        time.sleep(5) 

        print("🎯 [PASSO 3] Extraindo link da casa de aposta...")
        
        # O HTML que você mandou mostra que o link está na classe 'wcl-bookmakerLogo_4IUU0'
        # Vamos pegar o segundo logo (geralmente Betano/Superbet)
        logos = driver.find_elements(By.XPATH, "//div[contains(@class, 'wcl-bookmakerLogo')]//a")
        
        if len(logos) >= 2:
            link_transicao = logos[1].get_attribute("href") # Pega o segundo logo da lista
            print(f"📊 [LOG] Link extraído do logo: {link_transicao[:70]}...")
            
            print("⏳ [PASSO 4] Navegando para o redirecionamento...")
            driver.get(link_transicao)
        else:
            # Backup caso só tenha uma casa
            link_transicao = logos[0].get_attribute("href")
            driver.get(link_transicao)

        # PASSO 5: Redirecionamento Final
        print("📡 Monitorando redirecionamento final...")
        url_final = ""
        for i in range(30):
            url_atual = driver.current_url
            # Verifica se saiu do flashscore e entrou no domínio da aposta
            if "flashscore" not in url_atual and ("betano" in url_atual or "superbet" in url_atual):
                url_final = url_atual
                print("✨ Sucesso! Domínio atingido.")
                break
            time.sleep(1)

        print(f"\n✅ [PASSO 5] RESULTADO FINAL:")
        print(f"🔗 {url_final if url_final else url_atual}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    URL_ALVO = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_final(URL_ALVO)
    
