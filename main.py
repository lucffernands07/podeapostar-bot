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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def analisar_detalhes_h2h(driver, id_jogo, confronto):
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    driver.execute_script(f"window.open('{url_h2h}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(2)
        
        print(f"\n--- Analisando: {confronto} ---")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            time_nome = "Mandante" if i == 0 else "Visitante"
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                # Resultados V/E/D
                try:
                    status = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                    if not status:
                        title = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").get_attribute("title").lower()
                        status = "V" if "vitória" in title else "D" if "derrota" in title else "E"
                    stats["h"].append(status)
                except: stats["h"].append("?")

                # Placares e Gols
                try:
                    placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "").strip()
                    stats["placares"].append(placar)
                    gols = [int(g) for g in placar.split("-") if g.strip().isdigit()]
                    if sum(gols) > 1.5: stats["15"] += 1
                    if sum(gols) > 2.5: stats["25"] += 1
                except: pass
            
            # Print do Log para o GitHub
            print(f"[{time_nome}] Histórico: {'-'.join(stats['h'])}")
            print(f"[{time_nome}] Placares: {' | '.join(stats['placares'])}")
            print(f"[{time_nome}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")

        print(f"Etapa 2: Coletado informações do jogo {confronto} ✅")
        
    except Exception as e:
        print(f"Etapa 2: Sem informações do jogo {confronto} ❌ (Erro: {str(e)})")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    print("Etapa 1: Busca de jogos do dia ✅")
    
    try:
        driver.get(URL_LIBERTADORES)
        time.sleep(10)
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        for el in elementos:
            try:
                id_jogo = el.get_attribute("id").split("_")[-1]
                tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                h_utc = tempo_raw.split()[-1]
                h_obj = datetime.strptime(h_utc, "%H:%M")
                
                times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"

                aceitar = False
                if amanha_no_site in tempo_raw:
                    if h_obj.hour <= 3: aceitar = True
                elif "." not in tempo_raw:
                    if (h_obj - timedelta(hours=3)).hour >= 11: aceitar = True

                if aceitar:
                    analisar_detalhes_h2h(driver, id_jogo, confronto)
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                    
