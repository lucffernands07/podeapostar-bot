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
        # PASSO 1: Entrar na URL H2H (Usando a URL exata que você forneceu)
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        # PASSO 2: Localizar seção de Odds
        print("🔍 [PASSO 2] Localizando seção de Odds...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'section__prematchOdds')]")))
        time.sleep(5) 

        # PASSO 3: Clicar no primeiro decimal da Betano
        print("🎯 [PASSO 3] Localizando decimal da Betano...")
        
        # Captura todos os valores decimais da tela (Método que deu log de 2.88 antes)
        all_odds = driver.find_elements(By.XPATH, "//span[@data-testid='wcl-oddsValue']")
        
        if len(all_odds) >= 4:
            # Pulando as 3 odds da Bet365, a 4ª [índice 3] deve ser a da Betano
            odd_alvo = all_odds[3] 
            print(f"📊 [LOG] Odd detectada (4ª na lista): {odd_alvo.text}")
            
            # Clique via JS para evitar erros de renderização
            driver.execute_script("arguments[0].click();", odd_alvo)
        else:
            print(f"⚠️ Lista curta (apenas {len(all_odds)} encontradas). Tentando clicar na primeira.")
            driver.execute_script("arguments[0].click();", all_odds[0])

        # PASSO 4: Esperar trocar o domínio da URL
        print("⏳ [PASSO 4] Aguardando troca de domínio (Flashscore -> Betano)...")
        
        # Aguarda a abertura da nova aba
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        url_final = ""
        for i in range(25):
            atual = driver.current_url
            if i % 5 == 0: print(f"   📡 URL em transição: {atual[:50]}...")
            
            # Critério de sucesso: Domínio Betano presente e Flashscore ausente
            if "betano.com" in atual and "flashscore" not in atual:
                url_final = atual
                print(f"   ✨ Sucesso! Redirecionamento completo.")
                break
            time.sleep(1)

        # PASSO 5: Mostrar o resultado final
        print(f"\n✅ [PASSO 5] RESULTADO DA URL:")
        print(f"🔗 {url_final if url_final else driver.current_url}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
        driver.save_screenshot("debug_erro_nacional.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    # URL ATUALIZADA conforme sua solicitação
    url_teste = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_final(url_teste)
        
