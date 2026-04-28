import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # --- LÓGICA ANTI-BLOQUEIO (DICA DO SOFASCORE) ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Remove o rastro do Selenium no JavaScript (crucial!)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def buscar_link_via_google(time_casa, time_fora):
    driver = configurar_driver()
    # Mudando para uma URL de busca que parece mais 'orgânica'
    termo = f"betano odds {time_casa} vs {time_fora}".replace(" ", "+")
    url_google = f"https://www.google.com/search?q={termo}&num=10"
    url_final = None

    try:
        print(f"🚀 Iniciando busca stealth: {time_casa} x {time_fora}")
        driver.get(url_google)
        time.sleep(5) # O Google demora mais para processar o 'Stealth' no headless

        # Captura todos os links de resultados (seletor de link do Google é o 'a')
        elementos_a = driver.find_elements(By.CSS_SELECTOR, "a")
        
        links_validados = []
        for el in elementos_a:
            href = el.get_attribute("href")
            if href and "betano.bet.br/odds/" in href:
                # Se o link tiver o nome do time ou 'jogos', é o nosso alvo
                if time_casa.lower()[:5] in href.lower() or "jogos" in href.lower():
                    links_validados.append(href)

        if links_validados:
            # Pegamos o primeiro link da lista de achados
            escolhido = links_validados[0]
            print(f"🎯 Achamos! {escolhido}")
            
            # Navega para a Betano para pegar a URL final limpa
            driver.get(escolhido)
            time.sleep(4)
            url_final = driver.current_url
            print(f"✅ URL Final Capturada: {url_final}")
        else:
            # Se não achou nada, vamos imprimir o título da página para saber se caímos em Captcha
            print(f"❌ Falha. Título da página: {driver.title}")
            if "Google" not in driver.title:
                print("⚠️ Provavelmente fomos bloqueados ou redirecionados.")

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    finally:
        driver.quit()
        return url_final

if __name__ == "__main__":
    print("=== TESTE STEALTH (Lógica SofaScore) ===")
    resultado = buscar_link_via_google("Cruzeiro", "Boca Juniors")
    
    print("\n" + "="*50)
    if resultado:
        print(f"URL: {resultado}")
    else:
        print("FALHA: Tente ajustar o User-Agent ou o tempo de espera.")
    print("="*50)
    
