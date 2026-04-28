import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    # options.add_argument("--headless") # Desative o headless se quiser ver o Chrome trabalhando
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def buscar_link_via_google(time_casa, time_fora):
    driver = configurar_driver()
    termo_busca = f"Betano {time_casa} x {time_fora}"
    url_final = None

    try:
        print(f"🚀 Iniciando busca no Google para: {time_casa} x {time_fora}")
        driver.get("https://www.google.com")
        
        # 1. Pesquisa no Google
        wait = WebDriverWait(driver, 10)
        campo_google = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        campo_google.send_keys(termo_busca)
        campo_google.send_keys(Keys.ENTER)

        # 2. Localiza o primeiro link que contenha "betano.bet.br/odds/"
        print("🔍 Filtrando resultados da Betano...")
        links_resultados = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
        
        link_betano = None
        for a in links_resultados:
            href = a.get_attribute("href")
            if href and "betano.bet.br/odds/" in href:
                link_betano = href
                break
        
        if link_betano:
            print(f"🔗 Link encontrado no Google: {link_betano}")
            # 3. Abre o link para validar
            driver.get(link_betano)
            time.sleep(3) # Espera carregar a página da Betano
            
            # 4. Copia a URL real da barra de endereços
            url_final = driver.current_url
            print(f"✅ URL Capturada com sucesso: {url_final}")
        else:
            print("❌ Nenhum link da Betano encontrado nos primeiros resultados do Google.")

    except Exception as e:
        print(f"⚠️ Erro durante o teste: {e}")
    
    finally:
        driver.quit()
        return url_final

# --- EXECUÇÃO DO TESTE ---
if __name__ == "__main__":
    # Teste com o jogo que você mencionou
    resultado = buscar_link_via_google("Cruzeiro", "Boca Juniors")
    
    print("\n" + "="*30)
    if resultado:
        print(f"RESULTADO FINAL: {resultado}")
    else:
        print("RESULTADO FINAL: Falha ao obter link.")
    print("="*30)
