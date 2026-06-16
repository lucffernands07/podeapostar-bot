import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def testar_captura_chutes():
    url_h2h_teste = "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/"
    driver = configurar_driver()
    
    try:
        driver.get(url_h2h_teste)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        # Seleciona a primeira tabela e a primeira linha
        tabela_1 = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")[0]
        primeira_linha = tabela_1.find_element(By.CSS_SELECTOR, ".h2h__row")
        
        # --- Lógica do "Toque Segurado" ---
        link_elemento = primeira_linha.find_element(By.CSS_SELECTOR, "a")
        url_capturada = link_elemento.get_attribute("href")
        
        match = re.search(r'-([a-zA-Z0-9]{8})', url_capturada)
        if not match:
            raise Exception("Falha ao extrair ID")
            
        id_jogo = match.group(1)
        # ----------------------------------
        
        print(f"2. ✅ ID isolado via leitura de link: {id_jogo}")
        
        # Monta a URL final exatamente como você pediu
        url_final = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
        
        print(f"3. ✅ Acessando URL: {url_final}")
        driver.get(url_final)
        time.sleep(5)
        
        print("\n🎉 SUCESSO! Chegamos na página de finalizações.")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_captura_chutes()
    
