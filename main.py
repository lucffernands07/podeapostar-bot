import os
import time
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
    options.add_argument("--window-size=1920,3000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extrair_dados_h2h(driver, id_jogo, confronto):
    # Abrimos a página principal do resumo
    url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 25)
        
        # 1. Tenta clicar no botão H2H de várias formas (Texto ou Atributo)
        try:
            # Espera o container das abas carregar
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".tabs__detail--anchors")))
            # Clica no botão que contém o texto H2H
            aba_h2h = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'H2H')] | //button[contains(., 'H2H')]")))
            driver.execute_script("arguments[0].click();", aba_h2h)
            print(f"Clique na aba H2H realizado para: {confronto}")
        except Exception as e:
            print(f"Não consegui clicar no botão H2H de {confronto}. Tentando URL direta...")
            driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")

        # 2. Espera carregar a tabela H2H
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(5) 
        
        print(f"\n--- 📊 EXTRAÇÃO: {confronto} ---")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            time_nome = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                try:
                    icon = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                    res = icon.text.strip() or icon.get_attribute("title")[0].upper()
                    
                    gols_spans = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                    g1 = int(gols_spans[0].text.strip())
                    g2 = int(gols_spans[1].text.strip())
                    
                    stats["h"].append(res)
                    stats["placares"].append(f"{g1}-{g2}")
                    if (g1 + g2) > 1.5: stats["15"] += 1
                    if (g1 + g2) > 2.5: stats["25"] += 1
                except: continue
            
            print(f"[{time_nome}] Histórico: {'-'.join(stats['h'])}")
            print(f"[{time_nome}] Placares: {' | '.join(stats['placares'])}")
            print(f"[{time_nome}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")

    except Exception as e:
        print(f"Erro na extração de {confronto}: {str(e)}")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(12)
        
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        for el in elementos:
            # Pula se tiver placar (já começou)
            if any(s.text.strip() != "" for s in el.find_elements(By.CSS_SELECTOR, ".event__score")): continue
            
            try:
                status_texto = el.text
                # Se encontrar o Sporting Cristal ou qualquer jogo com horário (:)
                if ":" in status_texto:
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"
                    extrair_dados_h2h(driver, id_jogo, confronto)
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
