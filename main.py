import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def capturar_bruto_estatisticas(driver, id_jogo, label):
    url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
    print(f"\n--- [LOG BRUTO] {label} (ID: {id_jogo}) ---")
    
    driver.get(url_jogo)
    try:
        # Tenta clicar na aba Estatísticas
        btn_stats = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Estatísticas')]"))
        )
        driver.execute_script("arguments[0].click();", btn_stats)
        
        # Aguarda renderização
        time.sleep(5)
        
        # Captura o texto de todo o card de estatísticas
        container = driver.find_element(By.CSS_SELECTOR, "div[id*='statistics']")
        
        # CORREÇÃO DA SINTAXE: Processa fora da f-string
        texto_limpo = container.text.replace('\n', ' | ')
        print(f"CONTEUDO_BRUTO: {texto_limpo}")
        
    except Exception as e:
        print(f"⚠️ Sem estatísticas para {id_jogo} ou erro: {e}")

def main():
    driver = configurar_driver()
    id_principal = "ne5y23mR" 
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_principal}/#/h2h/overall"
    
    print(f"🚀 INICIANDO CAPTURA ÚNICA - JOGO: {id_principal}")
    
    try:
        driver.get(url_h2h)
        time.sleep(8)
        
        ids_alvo = []
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]):
            try:
                # Pega apenas o primeiro jogo (o mais recente)
                primeira_linha = secao.find_element(By.CSS_SELECTOR, ".h2h__row")
                id_raw = primeira_linha.get_attribute("id").split('_')[-1]
                ids_alvo.append(id_raw)
            except:
                pass

        if len(ids_alvo) >= 1:
            # Captura o bruto do último jogo do Casa (Defensa)
            capturar_bruto_estatisticas(driver, ids_alvo[0], "ÚLTIMO JOGO CASA")
            
            # Captura o bruto do último jogo do Fora (Boca), se existir
            if len(ids_alvo) > 1:
                capturar_bruto_estatisticas(driver, ids_alvo[1], "ÚLTIMO JOGO FORA")
        else:
            print("❌ Falha ao localizar os IDs no H2H.")

    finally:
        print("\n🏁 FIM DO DIAGNÓSTICO.")
        driver.quit()

if __name__ == "__main__":
    main()
    
