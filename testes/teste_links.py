import sys
import os
import time

# Garante que o script consiga importar módulos da raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    options.add_argument("--headless") # Essencial para rodar no GitHub Actions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # User-agent para o Google não desconfiar que é um bot básico
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def buscar_link_via_google(time_casa, time_fora):
    driver = configurar_driver()
    # Termo de busca focado na Betano
    termo_busca = f"site:betano.bet.br/odds {time_casa} x {time_fora}"
    url_final = None

    try:
        print(f"🚀 Iniciando busca no Google: {time_casa} x {time_fora}")
        driver.get("https://www.google.com")
        
        # Aceitar cookies do Google se aparecer (comum em servidores gringos)
        try:
            btn_aceitar = driver.find_element(By.XPATH, "//button[contains(., 'Aceitar')]")
            btn_aceitar.click()
        except:
            pass

        # 1. Realiza a pesquisa
        wait = WebDriverWait(driver, 15)
        campo_google = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        campo_google.send_keys(termo_busca)
        campo_google.send_keys(Keys.ENTER)

        # 2. Captura os links dos resultados
        print("🔍 Filtrando resultados...")
        time.sleep(2)
        links_resultados = driver.find_elements(By.CSS_SELECTOR, "a")
        
        link_encontrado = None
        for a in links_resultados:
            href = a.get_attribute("href")
            if href and "betano.bet.br/odds/" in href:
                # Evita links de categorias gerais, foca no link do jogo
                if "-jogos/" in href or any(char.isdigit() for char in href):
                    link_encontrado = href
                    break
        
        if link_encontrado:
            print(f"🔗 Link direto encontrado: {link_encontrado}")
            # 3. Navega até o link para confirmar que não é 404
            driver.get(link_encontrado)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            url_final = driver.current_url
            print(f"✅ URL Validada: {url_final}")
        else:
            print("❌ Nenhum link específico da Betano foi encontrado nos resultados.")

    except Exception as e:
        print(f"⚠️ Ocorreu um erro no teste: {str(e)}")
    
    finally:
        driver.quit()
        return url_final

# --- TESTE DE EXECUÇÃO ---
if __name__ == "__main__":
    print("=== INICIANDO TESTE ISOLADO ===")
    
    # Podemos testar o jogo que você teve problema
    casa = "Cruzeiro"
    fora = "Boca Juniors"
    
    resultado = buscar_link_via_google(casa, fora)
    
    print("\n" + "="*50)
    if resultado:
        print(f"SUCESSO: {resultado}")
    else:
        print("FALHA: O link não pôde ser obtido.")
    print("="*50)
            
