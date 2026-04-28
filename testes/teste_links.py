import sys
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Garante que encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def buscar_link_via_google(time_casa, time_fora):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # O UC já cuida da maioria dos bloqueios sozinho, mas vamos garantir:
    termo = f"site:betano.bet.br/odds {time_casa} x {time_fora}"
    url_final = None

    try:
        print(f"🚀 [UC MODE] Iniciando busca potente: {time_casa} x {time_fora}")
        
        # O undetected_chromedriver não usa o Service do ChromeDriverManager comum
        driver = uc.Chrome(options=options, version_main=124) # Ajuste a versão se necessário

        driver.get("https://www.google.com")
        time.sleep(3)

        # 1. Pesquisa (Simulando digitação humana)
        search_box = driver.find_element(By.NAME, "q")
        for char in termo:
            search_box.send_keys(char)
            time.sleep(0.05)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(5)

        # 2. Captura de links
        links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            href = link.get_attribute("href")
            if href and "betano.bet.br/odds/" in href:
                if "-" in href:
                    print(f"✅ Link interceptado: {href}")
                    url_final = href
                    break

    except Exception as e:
        print(f"⚠️ Erro no UC: {e}")
    finally:
        try:
            driver.quit()
        except: pass
        return url_final

if __name__ == "__main__":
    print("=== TESTE COM UNDETECTED-CHROMEDRIVER ===")
    res = buscar_link_via_google("Cruzeiro", "Boca Juniors")
    print("\n" + "="*50)
    print(f"RESULTADO FINAL: {res if res else 'BLOQUEIO TOTAL'}")
    print("="*50)
    
