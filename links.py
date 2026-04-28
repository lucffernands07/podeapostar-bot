import sys
import os
import time

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
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Um User-Agent mais robusto
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def buscar_link_via_google(time_casa, time_fora):
    driver = configurar_driver()
    # Busca aberta, sem o prefixo "site:" para não ativar o alerta de bot
    termo_busca = f"Betano odds {time_casa} vs {time_fora}"
    url_final = None

    try:
        print(f"🚀 Iniciando busca aberta no Google: {time_casa} x {time_fora}")
        driver.get("https://www.google.com/search?q=" + termo_busca.replace(" ", "+"))
        
        wait = WebDriverWait(driver, 10)
        
        # 1. Pegar todos os links da página de resultados
        print("🔍 Analisando links da primeira página...")
        links_resultados = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        
        candidatos = []
        for a in links_resultados:
            href = a.get_attribute("href")
            if href:
                # Procura por qualquer link que seja da Betano e tenha 'odds'
                if "betano.bet.br" in href and "/odds/" in href:
                    # Se tiver o nome de um dos times no link, a chance de ser o certo é 99%
                    if time_casa.lower() in href.lower() or "jogos" in href.lower():
                        candidatos.append(href)
        
        if candidatos:
            # Pega o primeiro link da lista (geralmente o mais relevante)
            link_encontrado = candidatos[0]
            print(f"🔗 Link candidato encontrado: {link_encontrado}")
            
            # 2. Visita o link para confirmar
            driver.get(link_encontrado)
            time.sleep(3)
            url_final = driver.current_url
            print(f"✅ URL Confirmada: {url_final}")
        else:
            # Se falhar, tentamos uma busca alternativa
            print("❌ Nenhum link da Betano na primeira página. Tentando termo alternativo...")

    except Exception as e:
        print(f"⚠️ Erro no teste: {str(e)}")
    
    finally:
        driver.quit()
        return url_final

if __name__ == "__main__":
    print("=== TESTE ISOLADO V2 (Busca Aberta) ===")
    casa = "Cruzeiro"
    fora = "Boca Juniors"
    
    resultado = buscar_link_via_google(casa, fora)
    
    print("\n" + "="*50)
    print(f"RESULTADO: {resultado if resultado else 'FALHA'}")
    print("="*50)
    
