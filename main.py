import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_panathinaikos():
    browser = configurar_browser()
    # O link específico que você forneceu
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    print(f"🚀 Iniciando teste no link: {url_alvo}")
    
    try:
        browser.get(url_alvo)
        
        # Tempo crucial para os cards de H2H carregarem os dados de escanteio
        print("⏳ Aguardando 15 segundos para os spans carregarem...")
        time.sleep(15)
        
        # Busca pelos spans de estatística (conforme o print que você mandou)
        elementos = browser.find_elements(By.CLASS_NAME, "textStyle_table")
        
        mercado_encontrado = None
        
        for el in elementos:
            txt = el.text.strip()
            if txt:
                print(f"🔎 Analisando span: {txt}")
                # Verifica se é o span de escanteio (ex: "Menos do que 10.5 escanteios 10/10")
                if "escanteio" in txt.lower() and "10.5" in txt:
                    mercado_encontrado = txt
                    break
        
        if mercado_encontrado:
            msg = (
                "✅ *TESTE PANATHINAIKOS - SUCESSO*\n\n"
                f"🏟️ *Panathinaikos x Real Betis*\n"
                f"📊 Mercado Lido: `{mercado_encontrado}`\n"
                "---"
            )
            print(f"🔥 Sucesso! Enviando para o Telegram: {mercado_encontrado}")
        else:
            msg = "❌ *TESTE PANATHINAIKOS - FALHA*\n\nO robô acessou o site, mas não encontrou o span de 10.5 escanteios."
            print("❌ Falha: Span não encontrado.")

        # Envio para o Telegram
        url_tg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url_tg, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"⚠️ Erro no script: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    testar_panathinaikos()
