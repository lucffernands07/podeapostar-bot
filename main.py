import os
import time
from datetime import datetime
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

def analisar_detalhes_h2h(driver, id_jogo, confronto):
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    driver.execute_script(f"window.open('{url_h2h}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 25)
        # Espera carregar os containers de H2H
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".h2h__section")))
        driver.execute_script("window.scrollTo(0, 1000);") # Scroll para garantir renderização
        time.sleep(6) 
        
        print(f"\n--- 📊 EXTRAÇÃO DE DADOS: {confronto} ---")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            nome_time = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")
            contagem = 0
            for linha in linhas:
                if contagem >= 5: break # Queremos apenas as últimas 5
                
                try:
                    # 1. Resultado V/E/D
                    icon_el = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                    res = icon_el.text.strip()
                    if not res:
                        res = icon_el.get_attribute("title")[0].upper()
                    
                    # 2. Gols - Buscando os spans individuais do placar
                    gols_elementos = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                    if len(gols_elementos) >= 2:
                        g1 = int(gols_elementos[0].text.strip())
                        g2 = int(gols_elementos[1].text.strip())
                        soma = g1 + g2
                        
                        stats["h"].append(res)
                        stats["placares"].append(f"{g1}-{g2}")
                        if soma > 1.5: stats["15"] += 1
                        if soma > 2.5: stats["25"] += 1
                        contagem += 1
                except:
                    continue
            
            print(f"[{nome_time}] Histórico: {'-'.join(stats['h'])}")
            print(f"[{nome_time}] Placares: {' | '.join(stats['placares'])}")
            print(f"[{nome_time}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")
        
        print(f"Etapa 2: Coletado informações do jogo {confronto} ✅")
    except Exception as e:
        print(f"Etapa 2: Erro ao processar {confronto} ❌")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(12)
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        for el in elementos:
            # Ignora jogos com placar (ao vivo/encerrados)
            if any(s.text.strip() != "" for s in el.find_elements(By.CSS_SELECTOR, ".event__score")): continue
            
            try:
                tempo = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                if ":" in tempo:
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    analisar_detalhes_h2h(driver, id_jogo, confronto)
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
