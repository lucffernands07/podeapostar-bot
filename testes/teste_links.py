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
        # PASSO 1: Entrar na URL H2H
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        # PASSO 2: Localizar seção de Odds
        print("🔍 [PASSO 2] Localizando seção de Odds...")
        # Espera o container geral de odds aparecer
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'section__prematchOdds')]")))
        time.sleep(5) # Tempo extra para carregar os valores decimais

        # PASSO 3: Clicar no primeiro decimal da Betano
        # Baseado no que funcionou antes: vamos pegar a lista de todos os decimais
        print("🎯 [PASSO 3] Localizando decimal da Betano...")
        
        # Este seletor pega TODOS os valores decimais da tabela
        all_odds = driver.find_elements(By.XPATH, "//span[@data-testid='wcl-oddsValue']")
        
        if len(all_odds) >= 4:
            # Se a Bet365 tem 3 odds (1, X, 2), a 4ª odd [índice 3] é a primeira da Betano
            odd_alvo = all_odds[3] 
            print(f"📊 [LOG] Odd detectada (4ª na lista): {odd_alvo.text}")
            
            # Clique via JS
            driver.execute_script("arguments[0].click();", odd_alvo)
        else:
            # Backup caso a lista seja curta
            print("⚠️ Lista curta, tentando clicar na primeira disponível...")
            driver.execute_script("arguments[0].click();", all_odds[0])

        # PASSO 4: Esperar trocar o domínio
        print("⏳ [PASSO 4] Aguardando redirecionamento para Betano...")
        
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        url_final = ""
        for i in range(25): # Aumentei o tempo para 25s
            atual = driver.current_url
            # Imprime para você ver a troca na log
            if i % 5 == 0: print(f"   📡 Status URL: {atual[:50]}...")
            
            if "betano.com" in atual and "flashscore" not in atual:
                url_final = atual
                print(f"   ✨ Sucesso! Domínio atingido.")
                break
            time.sleep(1)

        # PASSO 5: Copiar a URL e mostrar na log
        print(f"\n✅ [PASSO 5] RESULTADO:")
        print(f"🔗 {url_final if url_final else driver.current_url}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    url_teste = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    executar_fluxo_final(url_teste)
            
