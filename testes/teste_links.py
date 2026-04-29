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

def executar_fluxo_extracao_direta(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,4000")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        # PASSO 1: Acessar o H2H
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        # PASSO 2: Localizar seção de Odds
        print("🔍 [PASSO 2] Aguardando carregamento das Odds...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'section__prematchOdds')]")))
        time.sleep(5) 

        # PASSO 3: Extrair o link de transição (kg-br.com)
        print("🎯 [PASSO 3] Extraindo link de transição da Betano...")
        
        # Localizamos a 4ª odd (Betano)
        all_odds = driver.find_elements(By.XPATH, "//span[@data-testid='wcl-oddsValue']")
        
        if len(all_odds) >= 4:
            odd_alvo = all_odds[3]
            print(f"📊 [LOG] Odd identificada: {odd_alvo.text}")
            
            # Buscamos o link (tag 'a') que envolve essa odd
            elemento_link = odd_alvo.find_element(By.XPATH, "./ancestor::a")
            link_transicao = elemento_link.get_attribute("href")
            
            if link_transicao:
                print(f"🔗 [LOG] Link de transição capturado: {link_transicao[:60]}...")
                
                # PASSO 4: Navegar direto pelo link (sem precisar clicar)
                print("⏳ [PASSO 4] Navegando direto para o link de transição...")
                driver.get(link_transicao)
            else:
                raise Exception("Atributo href não encontrado no elemento pai.")
        else:
            raise Exception("Não foram encontradas odds suficientes.")

        # PASSO 5: Aguardar o redirecionamento final para a Betano
        print("📡 Aguardando redirecionamento final para Betano...")
        url_final = ""
        for i in range(25):
            url_atual = driver.current_url
            # Se a URL mudar de kg-br.com para betano.bet.br
            if "betano.bet.br" in url_atual or ("betano.com" in url_atual and "flashscore" not in url_atual):
                url_final = url_atual
                print("✨ Domínio final atingido!")
                break
            time.sleep(1)

        print(f"\n✅ [PASSO 5] SUCESSO! URL FINAL:")
        print(f"🔗 {url_final if url_final else url_atual}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # URL do jogo Nacional x Universitario
    URL_ALVO = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_extracao_direta(URL_ALVO)
    
