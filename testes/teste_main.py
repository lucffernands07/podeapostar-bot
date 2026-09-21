import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de raspagem do StatsHub
from testes.teste_raspagem_h2h import pegar_estatisticas_statshub

def configurar_driver():
    options = Options()
    
    # Flags essenciais para rodar sem crash no Linux / GitHub Actions
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    
    # User-Agent Linux (compatível com o ambiente do runner)
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def main():
    driver = configurar_driver()
    
    # URL de teste no StatsHub e metadados do confronto
    url_jogo_test = "https://www.statshub.com/fixture/lanus-vs-estudiantes-de-la-plata-mubbyl/383366"
    t1 = "Lanús"
    t2 = "Estudiantes"
    
    print(f"\n🚀 Iniciando teste de raspagem StatsHub...")
    print(f"🏟️ Jogo: {t1} x {t2}")
    print(f"🔗 URL: {url_jogo_test}\n")
    
    try:
        # Executa a raspagem dos últimos 5 jogos em Casa (Lanús) e Fora (Estudiantes)
        inicio_tempo = time.time()
        dados_jogo = pegar_estatisticas_statshub(driver, url_jogo_test, t1, t2)
        tempo_total = round(time.time() - inicio_tempo, 2)
        
        print("\n" + "="*50)
        print("📊 RESULTADOS EXTRAÍDOS (DICIONÁRIO 'STATS')")
        print("="*50)
        
        # Exibe o dicionário resultante formatado no console
        print(json.dumps(dados_jogo, indent=4, ensure_ascii=False))
        
        print("\n" + "="*50)
        print(f"⏱️ Raspagem concluída em {tempo_total}s")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Erro ao executar a raspagem de teste: {e}")
        
    finally:
        try:
            driver.quit()
            print("🔒 Driver do Selenium encerrado.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
