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

def executar_sequencia_exata(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3500")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    
    try:
        # PASSO 1: Entrar na URL H2H
        print(f"🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 30)

        # PASSO 2: Encontrar tabela/card de odds após o confronto direto
        print("🔍 [PASSO 2] Localizando seção de Odds após as tabelas H2H...")
        # Esperamos as tabelas H2H carregarem primeiro para garantir o scroll
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "h2h__section")))
        
        # Localiza o título "Odds" que marca o início do card
        xpath_card_odds = "//div[contains(@class, 'section__prematchOdds')]"
        card_odds = wait.until(EC.presence_of_element_located((By.XPATH, xpath_card_odds)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_odds)
        time.sleep(2)

        # PASSO 3: Clicar no primeiro decimal da Betano (pulando a linha da Bet365)
        print("🎯 [PASSO 3] Buscando a linha da Betano...")
        
        # XPath que pula a Bet365 e foca na linha da Betano para pegar o primeiro valor
        xpath_linha_betano = "//div[contains(@class, 'wcl-bettingProvider') and .//img[@alt='Betano']]"
        linha_betano = wait.until(EC.presence_of_element_located((By.XPATH, xpath_linha_betano)))
        
        # Pega o primeiro valor decimal desta linha específica
        xpath_primeira_odd_betano = ".//span[@data-testid='wcl-oddsValue'][1]"
        odd_element = linha_betano.find_element(By.XPATH, xpath_primeira_odd_betano)
        
        print(f"📊 [LOG] Odd da Betano detectada: {odd_element.text}")
        
        # Clique via JS para evitar sobreposição de elementos
        driver.execute_script("arguments[0].click();", odd_element)

        # PASSO 4: Esperar trocar o domínio de Flashscore para Betano
        print("⏳ [PASSO 4] Aguardando redirecionamento (Ponte Flashscore -> Betano)...")
        
        # Espera abrir a nova aba
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # Loop de verificação de domínio (máximo 15 segundos)
        url_final = ""
        for _ in range(15):
            url_atual = driver.current_url
            if "betano.com" in url_atual and "flashscore" not in url_atual:
                url_final = url_atual
                break
            time.sleep(1)
        
        # PASSO 5: Copiar e mostrar a URL na log
        if url_final:
            print(f"\n✅ [PASSO 5] SUCESSO! URL Final capturada:")
            print(f"🔗 {url_final}")
        else:
            print(f"⚠️ [PASSO 5] Timeout no redirecionamento. URL capturada: {driver.current_url}")

    except Exception as e:
        print(f"❌ Erro na sequência: {e}")
        driver.save_screenshot("erro_sequencia.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.flashscore.com.br/jogo/futebol/boca-juniors-hMrWAFH0/cruzeiro-0SwtclaU/h2h/total/?mid=KI37ibhD"
    executar_sequencia_exata(url)
        
