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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def testar_clique_pelo_nome():
    driver = configurar_driver()
    try:
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait = WebDriverWait(driver, 15)
        
        # Espera as linhas carregarem
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Procura o elemento que contém o nome "Irlanda do Norte" (usando XPath para buscar pelo texto)
        # Isso é infalível, não importa a estrutura do HTML
        elemento_jogo = driver.find_element(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
        
        # Clica no elemento encontrado
        print("🔄 Clicando na partida da Irlanda do Norte...")
        driver.execute_script("arguments[0].click();", elemento_jogo)
        
        # Aguarda a navegação completar
        time.sleep(5)
        
        # Captura a URL real
        url_final = driver.current_url
        print(f"🔗 URL capturada após o clique: {url_final}")
        
        # Agora só precisamos extrair o ID e formatar a URL das estatísticas
        # O ID está entre o último hífen antes do ?mid=
        import re
        match = re.search(r'-([a-zA-Z0-9]{8})', url_final)
        if match:
            id_real = match.group(1)
            url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
            print(f"3. ✅ URL alvo formatada: {url_estatisticas}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_clique_pelo_nome()
    
