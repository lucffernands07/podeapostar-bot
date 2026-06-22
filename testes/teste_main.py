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
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

if __name__ == "__main__":
    # Lista de jogos para teste
    LISTA_JOGOS = [
        "https://www.flashscore.com.br/jogo/futebol/novorizontino-4lOgZPQl/ponte-preta-WlHjRvDk/h2h/total/",
        "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/iraque-K8aAGt6r/h2h/total/"
    ]
    
    driver = configurar_driver()
    wait = WebDriverWait(driver, 10)
    stats = {"historico_chutes": {}}

    try:
        for i, url_h2h in enumerate(LISTA_JOGOS):
            print(f"\n🚀 --- TESTANDO JOGO {i+1}/{len(LISTA_JOGOS)} ---")
            print(f"🔗 URL: {url_h2h}")
            
            driver.get(url_h2h)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            
            # Pega a primeira linha de confronto
            elemento_jogo = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")[0]
            driver.execute_script("arguments[0].click();", elemento_jogo)
            
            # Aguarda a transição para a página do jogo (usando a mudança de URL)
            wait.until(lambda d: "/resumo" in d.current_url)
            url_jogo = driver.current_url.split("/resumo")[0]
            
            # Acessa Finalizações diretamente
            url_fin = f"{url_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
            driver.get(url_fin)
            
            # Aguarda carregar a tabela
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".wcl-table__row_")))
            
            # Mapeamento dinâmico de coluna (usando o índice 5 como fallback seguro)
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
            idx_chutes = 5 # Padrão para finalizações
            for idx, th in enumerate(cabecalhos):
                if "FN" in th.text or "ALVO" in th.text.upper():
                    idx_chutes = idx
                    break
            
            linhas = driver.find_elements(By.CSS_SELECTOR, ".wcl-table__row_")
            for linha in linhas:
                try:
                    nome = linha.find_element(By.CSS_SELECTOR, "[class*='playerName']").text.split('\n')[0]
                    cels = linha.find_elements(By.CSS_SELECTOR, "td")
                    if len(cels) > idx_chutes:
                        val = cels[idx_chutes].text
                        qtd = int(val) if val.isdigit() else 0
                        
                        if nome not in stats["historico_chutes"]:
                            stats["historico_chutes"][nome] = [0] * i # Preenche com 0 jogos anteriores
                        stats["historico_chutes"][nome].append(qtd)
                        print(f"Atleta: {nome} | Chutes: {qtd}")
                except: continue

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")
