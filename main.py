import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_teste_aba_partidas():
    browser = configurar_browser()
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    status = {"aba": "❌ Não clicou", "span": "❌ Não encontrado"}
    
    try:
        browser.get(url_alvo)
        wait = WebDriverWait(browser, 20)
        
        print("🖱️ Tentando clicar na aba 'Partidas'...")
        # Localiza pelo href que você indicou ou pelo texto do link
        try:
            # Tenta clicar pelo seletor de link que você passou
            aba_partidas = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba_partidas) # Click via JS é mais garantido
            status["aba"] = "✅ Aba Partidas Acessada"
            print("✅ Clique na aba realizado.")
        except:
            print("⚠️ Não achou o link pelo CSS, tentando por texto...")
            aba_partidas = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Partidas')] | //a[contains(., 'Partidas')]")))
            aba_partidas.click()
            status["aba"] = "✅ Aba Partidas Acessada (via texto)"

        # Aguarda os cards de H2H/Tendências carregarem dentro da aba
        time.sleep(10)
        
        print("🔎 Buscando span de escanteios...")
        # Busca o span específico que você mapeou anteriormente
        spans = browser.find_elements(By.CLASS_NAME, "textStyle_table")
        
        for s in spans:
            txt = s.text.strip()
            if "10.5" in txt and "escanteio" in txt.lower():
                status["span"] = f"✅ Encontrado: {txt}"
                print(f"🔥 SUCESSO: {txt}")
                break

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    finally:
        browser.quit()

    # Relatório para o Telegram
    msg = (
        "🧪 *TESTE DE ABA SOFASCORE*\n\n"
        f"📍 *Status Aba:* {status['aba']}\n"
        f"📈 *Resultado Span:* `{status['span']}`"
    )
    
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    executar_teste_aba_partidas()
