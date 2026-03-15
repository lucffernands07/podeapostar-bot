import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new") # Obrigatório para GitHub Actions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_diagnostico_estilo_repo(time_casa):
    driver = configurar_browser()
    print(f"\n🚀 --- INICIANDO TESTE ESTILO REPO: {time_casa} ---")
    
    try:
        # 1. ACESSA A HOME DO SOFASCORE
        driver.get("https://www.sofascore.com/pt/")
        print("✅ LOG: Home carregada.")
        time.sleep(6)

        # 2. LOCALIZA O LINK DO JOGO (Usando a lógica de busca do repo)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        link_jogo = None
        # O repo usa classes dinâmicas, vamos buscar por links que contenham o nome do time
        for a in soup.find_all('a', href=True):
            if time_casa.lower() in a.text.lower() and '/evento/' in a['href']:
                link_jogo = "https://www.sofascore.com" + a['href']
                break
        
        if not link_jogo:
            print(f"❌ LOG: Jogo '{time_casa}' não encontrado na lista.")
            return

        print(f"✅ LOG: Link do jogo encontrado: {link_jogo}")

        # 3. VAI PARA A ABA PARTIDAS (H2H)
        url_h2h = link_jogo + "#tab:matches"
        driver.get(url_h2h)
        print("⏳ LOG: Aguardando carregamento dos blocos de estatísticas...")
        
        # Simula o scroll do repositório para garantir que o JS carregue
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(10)

        # 4. RASPAGEM COM BEAUTIFULSOUP (Mais estável que Selenium puro)
        soup_h2h = BeautifulSoup(driver.page_source, 'html.parser')
        texto_pagina = soup_h2h.get_text(separator=' ')
        
        # 5. BUSCA PELAS FRAÇÕES 10.5
        matches = list(re.finditer(r"10\.5\s+escanteios", texto_pagina, re.IGNORECASE))
        print(f"\n📊 LOG: Encontrados {len(matches)} blocos de 10.5 escanteios.")

        frequencias = []
        for i, m in enumerate(matches, 1):
            trecho = texto_pagina[m.end() : m.end() + 60]
            frequencia = re.search(r"(\d+)/(\d+)", trecho)
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)
                print(f"   📍 Posição {i}: {num}/{den} ({perc:.1f}%)")

        # 6. VALIDAÇÃO 7ª e 8ª
        if len(frequencias) >= 8:
            casa = frequencias[6]
            fora = frequencias[7]
            print(f"\n🏠 CASA (7ª): {casa:.1f}%")
            print(f"🚌 FORA (8ª): {fora:.1f}%")
            print(f"📈 MÉDIA: {(casa + fora)/2:.1f}%")
        else:
            print(f"\n⚠️ AVISO: Apenas {len(frequencias)} frações. O H2H pode estar incompleto.")

    except Exception as e:
        print(f"🚨 ERRO: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste Finalizado.")

if __name__ == "__main__":
    testar_diagnostico_estilo_repo("Como")
