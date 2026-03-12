import os
import requests
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configurações do Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_teste_final():
    send_telegram("🚀 *LOG:* Iniciando scanner de texto bruto...")
    browser = configurar_browser()
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    entradas_escanteio = []

    try:
        # --- LOG 1: ACESSO ---
        browser.get(url_confronto)
        send_telegram(f"✅ *LOG 1:* URL acessada.")
        
        wait = WebDriverWait(browser, 25)
        
        # --- LOG 2: ABA PARTIDAS ---
        try:
            browser.execute_script("window.scrollTo(0, 500);")
            time.sleep(3)
            aba = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba)
            send_telegram("✅ *LOG 2:* Aba 'Partidas' aberta.")
        except Exception as e:
            send_telegram(f"⚠️ *LOG 2:* Erro na aba: {str(e)[:40]}")

        # Tempo para carregar os dados de H2H
        time.sleep(15)
        
        # --- LOG 3: EXTRAÇÃO VIA SCANNER (REGEX) ---
        # Pegamos todo o texto da página de uma vez
        corpo_pagina = browser.find_element(By.TAG_NAME, "body").text
        
        # O padrão busca: "Menos/Mais" + "do que 10.5 escanteios" + "qualquer coisa" + "fração (10/10)"
        # Esse padrão ignora se houver barras (|) ou espaços no meio
        padrao = r'(Menos|Mais)\s+do\s+que\s+10\.5\s+escanteios\s+.*?(\d+/\d+)'
        
        resultados = re.findall(padrao, corpo_pagina, re.IGNORECASE | re.DOTALL)

        if resultados:
            for item in resultados:
                tipo, freq = item
                # Limpamos o texto para o Telegram
                entradas_escanteio.append(f"🚩 *{tipo.capitalize()} do que 10.5 escanteios*\n📊 Frequência: *{freq}*")
        
        # Se o Regex falhar, tentamos uma busca direta por "escanteios" e pegamos os caracteres seguintes
        if not entradas_escanteio:
            if "10.5 escanteios" in corpo_pagina:
                partes = corpo_pagina.split("10.5 escanteios")
                for p in partes[1:]: # Analisa o que vem depois da palavra
                    freq_match = re.search(r'(\d+/\d+)', p)
                    if freq_match:
                        entradas_escanteio.append(f"🚩 *Mercado 10.5 Escanteios*\n📊 Frequência: *{freq_match.group(1)}*")

        if entradas_escanteio:
            # Remove duplicados e junta as mensagens
            msg_final = "\n\n".join(list(set(entradas_escanteio)))
            send_telegram(f"✅ *LOG 3:* Sucesso!\n\n{msg_final}")
        else:
            send_telegram("❌ *LOG 3:* Texto de escanteios não encontrado no padrão esperado.")

    except Exception as e:
        send_telegram(f"🚨 *ERRO:* {str(e)}")
    finally:
        browser.quit()
        send_telegram("🏁 *LOG:* Teste finalizado.")

if __name__ == "__main__":
    executar_teste_final()
