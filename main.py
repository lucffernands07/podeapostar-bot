import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL_LIBERTADORES = "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/"

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
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(4) 
        
        print(f"\n--- 📊 EXTRAÇÃO DE DADOS: {confronto} ---")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            nome_time = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                try:
                    icon = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                    res = icon.text.strip() or icon.get_attribute("title")[0].upper()
                    stats["h"].append(res)
                except: stats["h"].append("?")

                try:
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    spans = res_el.find_elements(By.TAG_NAME, "span")
                    g1, g2 = (spans[0].text.strip(), spans[1].text.strip()) if len(spans) >= 2 else res_el.text.split("-")
                    
                    stats["placares"].append(f"{g1}-{g2}")
                    if (int(g1) + int(g2)) > 1.5: stats["15"] += 1
                    if (int(g1) + int(g2)) > 2.5: stats["25"] += 1
                except: stats["placares"].append("?-?")
            
            print(f"[{nome_time}] Histórico: {'-'.join(stats['h'])}")
            print(f"[{nome_time}] Placares: {' | '.join(stats['placares'])}")
            print(f"[{nome_time}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")
        
        print(f"Etapa 2: Coletado informações do jogo {confronto} ✅")
    except:
        print(f"Etapa 2: Erro ao processar {confronto} ❌")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    try:
        driver.get(URL_LIBERTADORES)
        time.sleep(10)
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        for el in elementos:
            # NOVA TRAVA: Verifica se o jogo tem cronômetro (ex: 1', 32') ou placar preenchido
            stage = el.find_element(By.CSS_SELECTOR, ".event__stage").text.strip()
            scores = el.find_elements(By.CSS_SELECTOR, ".event__score")
            tem_placar = any(s.text.strip() != "" for s in scores)

            # Se tiver minuto (ex: 1') ou placar, descarta porque já começou
            if "'" in stage or tem_placar:
                continue

            # Se o jogo for futuro (ex: 23:00)
            if ":" in stage:
                times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"
                id_jogo = el.get_attribute("id").split("_")[-1]
                analisar_detalhes_h2h(driver, id_jogo, confronto)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
