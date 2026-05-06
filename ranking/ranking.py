import os
import time
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Caminhos
PATH_DB = "ranking/ranking_db.json"
PATH_PENDENTES = "ranking/pendentes.json"

def log(etapa, mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 ETAPA {etapa}: {mensagem}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def capturar_resultados_brutos():
    log(1, "Configurando driver (ChromeDriverManager)...")
    driver = configurar_driver()
    resultados_brutos = []

    try:
        log(2, "Acessando Flashscore.com.br...")
        driver.get("https://www.flashscore.com.br/")
        wait = WebDriverWait(driver, 20)

        # Passo 1: Clicar no botão 'ENCERRADOS'
        log(3, "Clicando no botão 'ENCERRADOS'...")
        btn_encerrados = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'ENCERRADOS')]")))
        btn_encerrados.click()
        time.sleep(2)

        # Passo 2: Abrir Calendário
        log(4, "Abrindo Day Picker...")
        btn_calendar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='wcl-dayPickerButton']")))
        btn_calendar.click()
        time.sleep(1)

        # Passo 3: Voltar para Ontem
        log(5, "Clicando na seta para data de ONTEM...")
        # Localiza o SVG da seta esquerda e clica no botão pai
        seta_esquerda = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".action-navigation-arrow-left")))
        driver.execute_script("arguments[0].closest('button').click();", seta_esquerda)
        time.sleep(5)

        log(6, "Extraindo jogos da tela...")
        eventos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        for evento in eventos:
            try:
                casa = evento.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                fora = evento.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()
                score_casa = evento.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                score_fora = evento.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()
                
                if score_casa != "" and score_fora != "":
                    resultados_brutos.append({
                        "confronto": f"{casa} x {fora}",
                        "placar": f"{score_casa}-{score_fora}",
                        "gols_casa": score_casa,
                        "gols_fora": score_fora
                    })
            except:
                continue

        log(7, f"Sucesso! {len(resultados_brutos)} jogos capturados.")

    except Exception as e:
        log("ERRO", f"Falha na captura: {e}")
    finally:
        driver.quit()
        log(8, "Driver encerrado.")

    return resultados_brutos

def main():
    log(0, "Iniciando Processo de Ranking")
    dados_site = capturar_resultados_brutos()
    
    # Exibe o JSON bruto para validação nos logs do GitHub
    log("FINAL", "JSON Bruto extraído:")
    print(json.dumps(dados_site, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
    
