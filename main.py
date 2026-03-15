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
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_diagnostico_ajustado(time_casa):
    driver = configurar_browser()
    print(f"\n🚀 --- INICIANDO TESTE REFORÇADO: {time_casa} ---")
    
    try:
        # 1. ACESSA A HOME
        driver.get("https://www.sofascore.com/pt/")
        print("✅ LOG: Home carregada. Aguardando lista completa...")
        time.sleep(10) # Tempo extra para carregar todos os campeonatos

        # 2. ROLAGEM AUTOMÁTICA (Para carregar jogos que estão mais abaixo, como a Série A)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # 3. BUSCA O LINK DO JOGO NO HTML COMPLETO
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        link_jogo = None
        
        # Procura por qualquer link que contenha o nome do time e a estrutura de evento
        for a in soup.find_all('a', href=True):
            texto = a.get_text().lower()
            href = a['href']
            if time_casa.lower() in texto and '/evento/' in href:
                link_jogo = "https://www.sofascore.com" + href
                break
        
        if not link_jogo:
            print(f"❌ LOG: Jogo '{time_casa}' não encontrado. Tentando busca direta...")
            # BACKUP: Se não achou na home, tenta o link de busca
            driver.get(f"https://www.sofascore.com/pt/busca?q={time_casa}")
            time.sleep(7)
            soup_busca = BeautifulSoup(driver.page_source, 'html.parser')
            for a in soup_busca.find_all('a', href=True):
                if '/evento/' in a['href']:
                    link_jogo = "https://www.sofascore.com" + a['href']
                    break

        if link_jogo:
            print(f"✅ LOG: Link encontrado: {link_jogo}")
            # 4. VAI PARA A ABA PARTIDAS
            driver.get(link_jogo + "#tab:matches")
            print("⏳ LOG: Aguardando carregamento do H2H...")
            time.sleep(12) 

            # 5. RASPAGEM FINAL
            soup_h2h = BeautifulSoup(driver.page_source, 'html.parser')
            texto_h2h = soup_h2h.get_text(separator=' ')
            
            matches = list(re.finditer(r"10\.5\s+escanteios", texto_h2h, re.IGNORECASE))
            print(f"\n📊 LOG: Encontrados {len(matches)} blocos de 10.5 escanteios.")

            frequencias = []
            for i, m in enumerate(matches, 1):
                trecho = texto_h2h[m.end() : m.end() + 60]
                frequencia = re.search(r"(\d+)/(\d+)", trecho)
                if frequencia:
                    num, den = int(frequencia.group(1)), int(frequencia.group(2))
                    perc = (num / den) * 100
                    frequencias.append(perc)
                    print(f"   📍 Posição {i}: {num}/{den} ({perc:.1f}%)")

            if len(frequencias) >= 8:
                print(f"\n🏠 CASA (7ª): {frequencias[6]:.1f}%")
                print(f"🚌 FORA (8ª): {frequencias[7]:.1f}%")
                print(f"📈 MÉDIA: {(frequencias[6] + frequencias[7])/2:.1f}%")
        else:
            print("❌ LOG: Jogo não localizado por nenhum método.")

    except Exception as e:
        print(f"🚨 ERRO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_diagnostico_ajustado("Como")
