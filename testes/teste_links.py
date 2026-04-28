import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def capturar_link_betano_via_flashscore(url_h2h):
    # Configuração do Driver para rodar no GitHub Actions
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    
    print(f"🚀 [ROBÔ] Acessando: {url_h2h}")
    
    try:
        driver.get(url_h2h)
        
        # 1. Espera o container de odds carregar (ajuste o tempo se necessário)
        wait = WebDriverWait(driver, 20)
        
        # 2. Localiza o botão da Betano usando o seu data-testid
        # Dica: O seletor que você passou é muito bom. 
        # Vamos buscar o elemento pai que é um link (<a>)
        # que contém esse span dentro.
        xpath_betano = "//div[contains(@class, 'wcl-bettingProvider')]//a[.//span[@data-testid='wcl-oddsValue']]"
        
        btn_betano = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_betano)))
        
        # 3. Clica para abrir na nova janela
        btn_betano.click()
        
        # 4. Espera a nova aba abrir e troca para ela
        time.sleep(3) # Pequena pausa para garantir que a aba carregou
        driver.switch_to.window(driver.window_handles[-1])
        
        # 5. Captura a URL final
        url_final = driver.current_url
        print(f"✅ URL exata da Betano capturada: {url_final}")
        return url_final

    except Exception as e:
        print(f"❌ Erro ao capturar link: {e}")
        # Opcional: salvar print para debug no GH Actions
        driver.save_screenshot("erro_captura.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Exemplo: URL do confronto direto do Flashscore
    # Substitua pela URL real do jogo que você quer testar
    url_teste = "https://www.flashscore.com.br/jogo/tXyZ1234/resumo" 
    resultado = capturar_link_betano_via_flashscore(url_teste)
    print(f"\nRESULTADO FINAL: {resultado}")
