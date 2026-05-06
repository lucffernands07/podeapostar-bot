import os
import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Caminhos de arquivos na pasta ranking
PATH_DB = "ranking/ranking_db.json"
PATH_PENDENTES = "ranking/pendentes.json"

def log(etapa, mensagem):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] 🚀 ETAPA {etapa}: {mensagem}")

def capturar_resultados_brutos():
    log(1, "Iniciando Undetected Chromedriver (Headless)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = uc.Chrome(options=options)
    resultados_brutos = []

    try:
        log(2, "Acessando Flashscore.com.br...")
        driver.get("https://www.flashscore.com.br/")
        wait = WebDriverWait(driver, 20)

        # Passo 1: Clicar no botão 'ENCERRADOS'
        log(3, "Tentando clicar no botão 'ENCERRADOS'...")
        # Localiza pelo texto conforme o print do layout
        btn_encerrados = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'ENCERRADOS')]")))
        btn_encerrados.click()
        time.sleep(2)

        # Passo 2: Clicar no seletor de data (Calendário)
        log(4, "Abrindo o seletor de data (Day Picker)...")
        btn_calendar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='wcl-dayPickerButton']")))
        btn_calendar.click()
        time.sleep(1)

        # Passo 3: Clicar na seta para a ESQUERDA (Dia Anterior)
        log(5, "Clicando na seta para voltar para a data de ONTEM...")
        seta_esquerda = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".action-navigation-arrow-left")))
        seta_esquerda.parent.click() # Clica no elemento pai da path SVG
        time.sleep(3) # Aguarda o carregamento dos jogos de ontem

        log(6, "Extraindo dados da lista de jogos...")
        
        # Localiza os containers de jogos
        eventos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        for evento in eventos:
            try:
                casa = evento.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                fora = evento.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()
                # Placar (pode variar se houver penaltis, pegamos o score principal)
                score_casa = evento.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                score_fora = evento.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()
                
                resultados_brutos.append({
                    "confronto": f"{casa} x {fora}",
                    "placar": f"{score_casa}-{score_fora}",
                    "gols_casa": score_casa,
                    "gols_fora": score_fora
                })
            except:
                continue

        log(7, f"Extração finalizada. Total de jogos encontrados: {len(resultados_brutos)}")

    except Exception as e:
        log("ERRO", f"Ocorreu uma falha durante a navegação: {str(e)}")
    
    finally:
        driver.quit()
        log(8, "Navegador encerrado.")

    return resultados_brutos

def main():
    log(0, "Iniciando processamento do Ranking Diário")
    
    # 1. Captura os dados reais do site
    dados_site = capturar_resultados_brutos()
    
    # 2. Mostra o JSON Bruto conforme solicitado
    log("FINAL", "Abaixo o JSON bruto extraído do Flashscore:")
    print(json.dumps(dados_site, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
