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

def extrair_dados_h2h(driver, id_jogo):
    # Caminho oficial: Abre o resumo e clica no H2H conforme você orientou
    url_resumo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
    driver.execute_script(f"window.open('{url_resumo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 25)
        
        # Localiza o nome dos times para o log
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".participant__participantName")))
        times_el = driver.find_elements(By.CSS_SELECTOR, ".participant__participantName")
        confronto = f"{times_el[0].text.strip()} x {times_el[1].text.strip()}"
        
        print(f"\n🚀 Processando: {confronto}")

        # Clica na aba H2H usando o seletor exato que você passou
        botao_h2h = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="wcl-tab"][role="tab"]')))
        driver.execute_script("arguments[0].click();", botao_h2h)
        
        # Espera a tabela carregar
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(5) 

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for i, secao in enumerate(secoes[:2]):
            time_nome = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                try:
                    icon = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                    gols = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                    g1, g2 = int(gols[0].text.strip()), int(gols[1].text.strip())
                    
                    stats["h"].append(icon or "?")
                    stats["placares"].append(f"{g1}-{g2}")
                    if (g1 + g2) > 1.5: stats["15"] += 1
                    if (g1 + g2) > 2.5: stats["25"] += 1
                except: continue
            
            print(f"   [{time_nome}] Histórico: {'-'.join(stats['h'])}")
            print(f"   [{time_nome}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")

    except Exception as e:
        print(f"❌ Erro nos detalhes do jogo {id_jogo}")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(12)
        
        # 1. Primeiro capturamos todos os IDs dos jogos agendados
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        ids_para_processar = []
        
        for el in elementos:
            # Pula se já tiver placar (já começou)
            if any(s.text.strip() != "" for s in el.find_elements(By.CSS_SELECTOR, ".event__score")):
                continue
            
            status = el.text
            if ":" in status: # Filtra por horário (ex: 19:00)
                jogo_id = el.get_attribute("id").split("_")[-1]
                ids_para_processar.append(jogo_id)
        
        print(f"Encontrados {len(ids_para_processar)} jogos para análise.")

        # 2. Agora iteramos sobre os IDs (isso evita o erro de Stale Element)
        for id_jogo in ids_para_processar:
            extrair_dados_h2h(driver, id_jogo)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                
