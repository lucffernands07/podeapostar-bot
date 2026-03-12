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

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_mineracao():
    send_telegram("🚀 *LOG:* Iniciando extração...")
    browser = configurar_browser()
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    entradas_escanteio = []

    try:
        # LOG 1: Acesso à URL
        browser.get(url_alvo)
        send_telegram(f"✅ *LOG 1:* Confronto acessado via URL: \n`{url_alvo}`")
        
        wait = WebDriverWait(browser, 20)
        
        # LOG 2: Tentar abrir a aba Partidas
        try:
            browser.execute_script("window.scrollTo(0, 400);")
            time.sleep(2)
            aba = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba)
            send_telegram("✅ *LOG 2:* Aba 'Partidas' encontrada e aberta com sucesso.")
        except Exception as e:
            send_telegram(f"⚠️ *LOG 2:* Falha ao clicar na aba 'Partidas'. Erro: {str(e)[:50]}")

        # Aguardar carregamento dos cards
        time.sleep(12)
        
        # LOG 3: Buscar valores de escanteios
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        for b in blocos:
            texto_bloco = b.text.strip()
            if "10.5 escanteio" in texto_bloco.lower():
                linhas = [l.strip() for l in texto_bloco.split('\n') if l.strip()]
                if len(linhas) >= 3 and "/" in linhas[-1]:
                    time_nome = linhas[0]
                    mercado = linhas[1]
                    frequencia = linhas[2]
                    entradas_escanteio.append(f"🚩 *{time_nome}* | {mercado} | Freq: {frequencia}")

        if entradas_escanteio:
            res_final = "\n".join(entradas_escanteio)
            send_telegram(f"✅ *LOG 3:* Valores de escanteios (10.5) encontrados:\n\n{res_final}")
        else:
            send_telegram("❌ *LOG 3:* Não foram encontrados cards de escanteios 10.5 após abrir a aba.")

    except Exception as e:
        send_telegram(f"🚨 *ERRO CRÍTICO:* {str(e)}")
    finally:
        browser.quit()
        send_telegram("🏁 *LOG:* Processo finalizado.")

if __name__ == "__main__":
    executar_mineracao()
