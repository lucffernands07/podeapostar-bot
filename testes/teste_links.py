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

        # PASSO 2: Encontrar tabela ou card de odds após a Tabela 3 (Confronto Direto)
        print("🔍 [PASSO 2] Localizando seção de Odds após o confronto direto...")
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "h2h__section")))
        
        # Localiza o marco das Odds
        xpath_odds_title = "//div[contains(@class, 'section__prematchOdds')]"
        titulo_odds = wait.until(EC.presence_of_element_located((By.XPATH, xpath_odds_title)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", titulo_odds)
        time.sleep(2)

        # PASSO 3: Clicar no primeiro decimal após a Bet365 (Focar na Betano)
        print("🎯 [PASSO 3] Localizando decimal da Betano (Pulando Bet365)...")
        
        odd_alvo = None
        
        # Tentativa 1: Via Link de Afiliado (Mais estável no headless)
        try:
            xpath_betano = "//a[contains(@href, 'betano')]//following::span[@data-testid='wcl-oddsValue'][1]"
            odd_alvo = driver.find_element(By.XPATH, xpath_betano)
            print("   ✅ Identificado via link 'betano'.")
        except:
            # Tentativa 2: Via Posição (Segunda linha da tabela de odds)
            try:
                xpath_posicao = "(//div[contains(@class, 'wcl-bettingProvider')])[2]//span[@data-testid='wcl-oddsValue'][1]"
                odd_alvo = driver.find_element(By.XPATH, xpath_posicao)
                print("   ✅ Identificado via posição (Linha 2).")
            except:
                # Tentativa 3: Varredura de Texto (Plano de Emergência)
                print("   ⚠️ Seletores falharam. Varrendo texto bruto...")
                providers = driver.find_elements(By.CLASS_NAME, "wcl-bettingProvider")
                for p in providers:
                    if "Betano" in p.text:
                        odd_alvo = p.find_element(By.XPATH, ".//span[@data-testid='wcl-oddsValue'][1]")
                        print("   ✅ Identificado via varredura de texto.")
                        break

        if odd_alvo:
            print(f"📊 [LOG] Odd da Betano encontrada: {odd_alvo.text}")
            # Clique via JS para garantir execução
            driver.execute_script("arguments[0].click();", odd_alvo)
        else:
            raise Exception("Não foi possível localizar a Betano no Passo 3.")

        # PASSO 4: Esperar trocar o domínio da URL de Flashscore para Betano
        print("⏳ [PASSO 4] Aguardando redirecionamento para o domínio Betano...")
        
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        url_final = ""
        for i in range(20):
            atual = driver.current_url
            if "betano.com" in atual and "flashscore" not in atual:
                url_final = atual
                print(f"   ✨ Domínio trocado com sucesso na tentativa {i+1}!")
                break
            time.sleep(1)

        # PASSO 5: Copiar a URL e mostrar na log
        if url_final:
            print(f"\n✅ [PASSO 5] URL CAPTURADA:")
            print(f"🔗 {url_final}")
        else:
            print(f"⚠️ [PASSO 5] Timeout: A URL não mudou a tempo. Atual: {driver.current_url}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
        driver.save_screenshot("erro_passo_a_passo.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url_teste = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    executar_fluxo_final(url_teste)
                    
