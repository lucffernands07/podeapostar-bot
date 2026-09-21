import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de raspagem do StatsHub
from funcoes.raspagem_h2h import pegar_estatisticas_statshub

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
    
    # User-Agent Linux
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def main():
    driver = configurar_driver()
    
    # LISTA DE JOGOS PARA RASPAGEM
    jogos_para_testar = [
        {
            "t1": "Lanús",
            "t2": "Estudiantes",
            "url": "https://www.statshub.com/fixture/lanus-vs-estudiantes-de-la-plata-mubbyl/383366"
        },
        {
            "t1": "Barracas Central",
            "t2": "Independiente Rivadavia",
            "url": "https://www.statshub.com/fixture/barracas-central-vs-independiente-rivadavia-mubbv9/383374"
        }
    ]
    
    resultados_totais = []
    inicio_tempo_total = time.time()
    
    print(f"\n🚀 Iniciando teste de raspagem StatsHub ({len(jogos_para_testar)} jogos na fila)...\n")
    
    try:
        for idx, jogo in enumerate(jogos_para_testar, 1):
            t1 = jogo["t1"]
            t2 = jogo["t2"]
            url = jogo["url"]
            
            print(f"--------------------------------------------------")
            print(f"🏟️ [{idx}/{len(jogos_para_testar)}] Processando: {t1} x {t2}")
            print(f"🔗 URL: {url}")
            print(f"--------------------------------------------------")
            
            try:
                inicio_jogo = time.time()
                dados_jogo = pegar_estatisticas_statshub(driver, url, t1, t2)
                tempo_jogo = round(time.time() - inicio_tempo_total if idx == 1 else time.time() - inicio_jogo, 2)
                
                resultados_totais.append({
                    "confronto": f"{t1} x {t2}",
                    "dados": dados_jogo
                })
                print(f"✅ Raspagem de {t1} x {t2} concluída em {tempo_jogo}s\n")
                
            except Exception as e_jogo:
                print(f"❌ Erro ao raspar {t1} x {t2}: {e_jogo}\n")
        
        tempo_total = round(time.time() - inicio_tempo_total, 2)
        
        print("\n" + "="*50)
        print("📊 RESULTADOS EXTRAÍDOS (LISTA CONSOLIDADA)")
        print("="*50)
        print(json.dumps(resultados_totais, indent=4, ensure_ascii=False))
        print("\n" + "="*50)
        print(f"⏱️ Raspagem total finalizada em {tempo_total}s")
        print("="*50 + "\n")
        
    finally:
        try:
            driver.quit()
            print("🔒 Driver do Selenium encerrado.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
