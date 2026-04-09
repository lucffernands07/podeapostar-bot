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
        # Espera robusta para garantir que a tabela carregue
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(5) # Tempo de respiro para renderização dos ícones
        
        print(f"\n--- 📊 EXTRAÇÃO DE DADOS: {confronto} ---")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            nome_time = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            # Busca as últimas 5 partidas
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                # 1. Captura V/E/D com fallback para o 'title' do ícone
                try:
                    icon_el = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                    res = icon_el.text.strip()
                    if not res:
                        title = icon_el.get_attribute("title").lower()
                        res = "V" if "vitória" in title else "D" if "derrota" in title else "E"
                    stats["h"].append(res)
                except: stats["h"].append("?")

                # 2. Captura Placares garantindo os dois lados do gol
                try:
                    res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result")
                    spans = res_el.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 2:
                        g1, g2 = spans[0].text.strip(), spans[1].text.strip()
                    else:
                        gols = [s for s in res_el.text.replace("\n", "-").split("-") if s.strip().isdigit()]
                        g1, g2 = gols[0], gols[1]
                    
                    stats["placares"].append(f"{g1}-{g2}")
                    soma = int(g1) + int(g2)
                    if soma > 1.5: stats["15"] += 1
                    if soma > 2.5: stats["25"] += 1
                except: stats["placares"].append("?-?")
            
            # Log detalhado para conferência das suas regras (5/5, 4/5...)
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
        driver.get(URL_LIBERTADORES)
        time.sleep(12)
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        for el in elementos:
            try:
                # Filtro de segurança: pula se tiver placar (já começou/acabou)
                if any(s.text.strip() != "" for s in el.find_elements(By.CSS_SELECTOR, ".event__score")):
                    continue

                # Pega horário e evita erros de elemento ausente
                try:
                    tempo = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                except: continue

                if ":" in tempo and "'" not in tempo:
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    analisar_detalhes_h2h(driver, id_jogo, confronto)
            except: continue
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                        
