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

def executar_teste_final():
    print("🚀 Iniciando extração de elite...")
    browser = configurar_browser()
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    entradas_escanteio = []

    try:
        browser.get(url_alvo)
        time.sleep(5)
        
        # 1. Forçar entrada na aba de Partidas (H2H)
        try:
            aba_partidas = browser.find_element(By.CSS_SELECTOR, 'a[href="#tab:matches"]')
            browser.execute_script("arguments[0].click();", aba_partidas)
            print("✅ Aba 'Partidas' clicada.")
        except:
            print("⚠️ Aba 'Partidas' não encontrada ou já selecionada.")

        # 2. Aguardar renderização dos cards
        time.sleep(12)
        
        # 3. Varredura dos blocos p_sm
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        
        for b in blocos:
            texto_bloco = b.text.strip()
            
            # FILTRO 1: Precisa ter a palavra 'escanteio'
            if "escanteio" in texto_bloco.lower() and "10.5" in texto_bloco:
                linhas = [l.strip() for l in texto_bloco.split('\n') if l.strip()]
                
                # FILTRO 2: Precisa ter o formato de fração (ex: 10/10) para não ser Odd
                if len(linhas) >= 3 and "/" in linhas[-1]:
                    time_nome = linhas[0]
                    mercado = linhas[1]
                    frequencia = linhas[2]
                    
                    entrada = (
                        f"🚩 *{time_nome}*\n"
                        f"🔸 {mercado}\n"
                        f"📊 Frequência: *{frequencia}*"
                    )
                    entradas_escanteio.append(entrada)
                    print(f"🔥 Capturado: {mercado} ({frequencia})")

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    finally:
        browser.quit()

    # 4. Envio para o Telegram
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    
    if entradas_escanteio:
        corpo = "\n\n".join(entradas_escanteio)
        msg = f"🎫 *BILHETE DE ESCANTEIOS (10.5)*\n🏟️ Panathinaikos x Real Betis\n\n{corpo}\n\n🍀 Boa sorte!"
    else:
        msg = "❌ Não foi possível isolar o mercado de escanteios (10.5) nos cards deste jogo."

    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    print("🏁 Teste finalizado e mensagem enviada.")

if __name__ == "__main__":
    executar_teste_final()
