import os
import time
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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
    # Desativa bloqueio de pop-ups para permitir a abertura da Betano
    options.add_argument("--disable-popup-blocking")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        # PASSO 1
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        # PASSO 2
        print("🔍 [PASSO 2] Localizando seção de Odds...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'section__prematchOdds')]")))
        time.sleep(5) 

        # PASSO 3: Clicar na Odd
        print("🎯 [PASSO 3] Localizando decimal da Betano...")
        all_odds = driver.find_elements(By.XPATH, "//span[@data-testid='wcl-oddsValue']")
        
        if len(all_odds) >= 4:
            odd_alvo = all_odds[3] 
            print(f"📊 [LOG] Odd detectada: {odd_alvo.text}")
            
            # TENTATIVA DE CLIQUE DUPLA:
            print("🖱️ Tentando clicar no seletor...")
            # 1. Tenta mover o mouse e clicar (simula humano)
            try:
                actions = ActionChains(driver)
                actions.move_to_element(odd_alvo).click().perform()
            except:
                # 2. Backup com JavaScript (força o clique se o anterior falhar)
                driver.execute_script("arguments[0].click();", odd_alvo)
        else:
            print("❌ Não encontrou odds suficientes na lista.")
            return

        # PASSO 4: Verificar Redirecionamento
        print("⏳ [PASSO 4] Aguardando troca de domínio...")
        
        # Espera até 15 segundos para a nova aba aparecer
        start_time = time.time()
        while len(driver.window_handles) == 1 and (time.time() - start_time) < 15:
            time.sleep(1)
            
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print(f"✅ Nova aba detectada! Monitorando URL...")
            
            url_final = ""
            for i in range(20):
                atual = driver.current_url
                if "betano.com" in atual and "flashscore" not in atual:
                    url_final = atual
                    break
                time.sleep(1)
            
            # PASSO 5
            print(f"\n✅ [PASSO 5] SUCESSO: {url_final if url_final else atual}")
        else:
            print("❌ Erro: O clique não abriu uma nova aba (Timeout).")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    url_teste = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_final(url_teste)
            
