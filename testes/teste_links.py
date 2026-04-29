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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-popup-blocking")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        print("🔍 [PASSO 2] Aguardando Odds carregarem...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'wclOddsRow')]")))
        time.sleep(5) 

        print("🎯 [PASSO 3] Localizando o botão da Odd Betano...")
        botoes_odds = driver.find_elements(By.XPATH, "//button[@data-testid='wcl-oddsCell']")
        
        if len(botoes_odds) >= 4:
            botao_alvo = botoes_odds[3] 
            print(f"📊 [LOG] Valor da Odd no botão: {botao_alvo.text.splitlines()[0]}")
            
            print("🖱️ Disparando clique forçado no botão...")
            driver.execute_script("arguments[0].click();", botao_alvo)
        else:
            print("❌ Botões de odd não encontrados.")
            return

        print("⏳ [PASSO 4] Aguardando abertura da aba da Betano...")
        nova_aba = False
        for _ in range(15):
            if len(driver.window_handles) > 1:
                nova_aba = True
                break
            time.sleep(1)

        if nova_aba:
            driver.switch_to.window(driver.window_handles[-1])
            
            url_suja = ""
            # Monitora até a URL conter o padrão de jogo da Betano
            for i in range(25):
                url_atual = driver.current_url
                if "match-odds" in url_atual:
                    url_suja = url_atual
                    print("✨ URL do Jogo detectada!")
                    break
                time.sleep(1)
            
            # --- LIMPEZA DA URL ---
            # Remove tudo o que vem depois do '?' ou '/' final se for lixo
            if url_suja:
                # Divide no '?' e pega a primeira parte (até o ID)
                url_limpa = url_suja.split('?')[0]
                # Garante que termina com uma barra
                if not url_limpa.endswith('/'):
                    url_limpa += '/'
                
                print(f"\n✅ [PASSO 5] SUCESSO! URL FINAL LIMPA:")
                print(f"🔗 {url_limpa}")
            else:
                print("❌ Falha ao capturar URL de jogo válida.")
        else:
            print("❌ Erro: O clique não abriu uma nova aba.")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    URL_ALVO = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_final(URL_ALVO)
