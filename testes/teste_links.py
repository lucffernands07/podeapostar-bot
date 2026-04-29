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

        # PASSO 3: Extrair o link de transição
        print("🎯 [PASSO 3] Localizando link da Betano pelo seletor de Odds...")
        
        # Localizamos todas as odds pelo data-testid que você confirmou
        all_odds = driver.find_elements(By.XPATH, "//span[@data-testid='wcl-oddsValue']")
        
        if len(all_odds) >= 4:
            odd_alvo = all_odds[3] # 4ª odd (Betano)
            print(f"📊 [LOG] Valor encontrado: {odd_alvo.text}")
            
            # NOVO MÉTODO DE BUSCA: 
            # Subimos 3 níveis (da span para a div, da div para o container e do container para o link)
            # Ou usamos um seletor de link que contenha esta odd específica
            try:
                # Tentativa 1: Ancestral genérico (qualquer link acima)
                link_transicao = odd_alvo.find_element(By.XPATH, "./ancestor::a").get_attribute("href")
            except:
                # Tentativa 2: Buscar o link pelo container da linha (mais robusto)
                # No Flashscore, as odds de uma casa ficam dentro de um container de linha
                print("⚠️ Falha no ancestral direto, tentando busca por container...")
                pai_odds = odd_alvo.find_element(By.XPATH, "../..") # Sobe dois níveis
                link_transicao = pai_odds.find_element(By.XPATH, ".//ancestor::a").get_attribute("href")

            if link_transicao:
                print(f"🔗 [LOG] Link extraído com sucesso: {link_transicao[:70]}...")
                
                # PASSO 4: Navegar
                print("⏳ [PASSO 4] Navegando para o redirecionamento...")
                driver.get(link_transicao)
            else:
                raise Exception("Link 'href' não encontrado nos níveis superiores.")
        else:
            raise Exception(f"Apenas {len(all_odds)} odds encontradas. Precisamos de pelo menos 4.")

        # PASSO 5: Redirecionamento Final
        print("📡 Monitorando redirecionamento para Betano...")
        url_final = ""
        for i in range(30): # 30 segundos de tolerância
            url_atual = driver.current_url
            if "betano.bet.br" in url_atual or ("betano.com" in url_atual and "flashscore" not in url_atual):
                url_final = url_atual
                print("✨ Domínio final atingido!")
                break
            time.sleep(1)

        print(f"\n✅ [PASSO 5] RESULTADO FINAL:")
        print(f"🔗 {url_final if url_final else url_atual}")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
        # Tira print do erro para debug se necessário
        driver.save_screenshot("erro_seletor.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    URL_ALVO = "https://www.flashscore.com.br/jogo/futebol/club-nacional-UaVu2MhA/universitario-xhw3JTnU/h2h/total/?mid=A9FCj3kT"
    executar_fluxo_extracao_direta(URL_ALVO)
    
