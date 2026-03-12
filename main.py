import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def minerar_escanteios_dual():
    browser = configurar_browser()
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    entradas = []

    try:
        browser.get(url_alvo)
        time.sleep(5)
        
        # Clica na aba Partidas (onde ficam as tendências de H2H)
        try:
            aba_partidas = browser.find_element(By.CSS_SELECTOR, 'a[href="#tab:matches"]')
            browser.execute_script("arguments[0].click();", aba_partidas)
        except: pass

        time.sleep(12) # Tempo para os cards carregarem
        
        # Varredura em todos os blocos de estatística p_sm
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        
        for b in blocos:
            texto = b.text
            if "10.5 escanteios" in texto:
                linhas = texto.split('\n')
                if len(linhas) >= 3:
                    time_nome = linhas[0]
                    mercado = linhas[1]
                    frequencia = linhas[2]
                    entradas.append(f"🚩 *{time_nome}*\n🔸 {mercado}\n📊 Frequência: *{frequencia}*")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        browser.quit()

    # ENVIO PARA O TELEGRAM
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    
    if entradas:
        corpo_msg = "\n\n".join(entradas)
        msg = f"🎫 *TENDÊNCIAS DE ESCANTEIOS*\n🏟️ Panathinaikos x Real Betis\n\n{corpo_msg}"
    else:
        msg = "❌ Não foi possível encontrar tendências de escanteio (10.5) para este confronto."

    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    minerar_escanteios_dual()
