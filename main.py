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
    options.add_argument("--headless")  # Mantenha headless para o GitHub Actions
    options.add_argument("--window-size=1920,3000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def processar_jogo(driver, elemento_jogo, confronto):
    try:
        # 1. Localiza o 'card' (link invisível) dentro do elemento do jogo
        card_clicavel = elemento_jogo.find_element(By.CSS_SELECTOR, "a.eventRowLink")
        id_jogo = elemento_jogo.get_attribute("id").split("_")[-1]
        
        print(f"\n🚀 Abrindo detalhes do jogo: {confronto} (ID: {id_jogo})")
        
        # 2. Clica para abrir a página do jogo em uma nova aba
        driver.execute_script("arguments[0].click();", card_clicavel)
        time.sleep(2)
        driver.switch_to.window(driver.window_handles[-1])
        
        wait = WebDriverWait(driver, 25)
        
        # 3. Clica no botão H2H usando o seletor exato que você passou
        # <button data-testid="wcl-tab" ...>H2H</button>
        botao_h2h = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="wcl-tab"][role="tab"]')))
        
        # Filtra pelo texto para garantir que é o H2H (caso existam outros botões com o mesmo testid)
        if "H2H" in botao_h2h.text:
            driver.execute_script("arguments[0].click();", botao_h2h)
            print(f"✅ Aba H2H clicada com sucesso.")
        
        # 4. Espera carregar a tabela e extrai os 5 jogos
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(4)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for i, secao in enumerate(secoes[:2]):
            time_nome = confronto.split(" x ")[i]
            stats = {"15": 0, "25": 0, "h": [], "placares": []}
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                try:
                    res = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                    gols = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                    g1, g2 = int(gols[0].text.strip()), int(gols[1].text.strip())
                    
                    stats["h"].append(res)
                    stats["placares"].append(f"{g1}-{g2}")
                    if (g1 + g2) > 1.5: stats["15"] += 1
                    if (g1 + g2) > 2.5: stats["25"] += 1
                except: continue
            
            print(f"   [{time_nome}] Histórico: {'-'.join(stats['h'])}")
            print(f"   [{time_nome}] Gols: +1.5 ({stats['15']}/5) | +2.5 ({stats['25']}/5)")

    except Exception as e:
        print(f"❌ Falha ao processar {confronto}")
    
    # Fecha a aba do jogo e volta para a lista principal
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def main():
    driver = configurar_driver()
    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(10)
        
        jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        for jogo in jogos:
            # Filtro: Apenas jogos agendados (sem placar)
            if any(s.text.strip() != "" for s in jogo.find_elements(By.CSS_SELECTOR, ".event__score")):
                continue
                
            info = jogo.text
            if ":" in info:
                times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                confronto = f"{times[0].text.strip()} x {times[1].text.strip()}"
                processar_jogo(driver, jogo, confronto)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
