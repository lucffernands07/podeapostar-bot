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

def minerar_organizado():
    browser = configurar_browser()
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    try:
        browser.get(url_confronto)
        wait = WebDriverWait(browser, 20)
        
        # 1. Abre a aba Partidas
        try:
            browser.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            aba = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba)
        except: pass

        time.sleep(15)
        
        # 2. Captura os nomes dos times no placar/topo para confirmar
        times_header = browser.find_elements(By.CLASS_NAME, "sc-6997034c-2") # Classe comum de nomes de times no Sofa
        nome_casa = "Casa"
        nome_fora = "Fora"
        if len(times_header) >= 2:
            nome_casa = times_header[0].text
            nome_fora = times_header[1].text

        # 3. Extração dos blocos de escanteio
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        dados_escanteio = []
        
        for b in blocos:
            texto = b.text.strip()
            if "10.5 escanteio" in texto.lower() and "/" in texto:
                # Pegamos apenas a frequência (ex: 10/10) e o mercado
                match_freq = re.search(r'(\d+/\d+)', texto)
                mercado = "Menos de 10.5" if "Menos" in texto else "Mais de 10.5"
                if match_freq:
                    dados_escanteio.append({"mercado": mercado, "freq": match_freq.group(1)})

        # 4. Montagem da Mensagem Final baseada na ordem (1º Casa, 2º Fora)
        if len(dados_escanteio) >= 2:
            msg = (
                f"🎫 *BILHETE DE ESCANTEIOS*\n"
                f"🏟️ {nome_casa} x {nome_fora}\n\n"
                f"🏠 *CASA:* {nome_casa}\n"
                f"🎯 {dados_escanteio[0]['mercado']}\n"
                f"📊 Frequência: *{dados_escanteio[0]['freq']}*\n\n"
                f"🚀 *FORA:* {nome_fora}\n"
                f"🎯 {dados_escanteio[1]['mercado']}\n"
                f"📊 Frequência: *{dados_escanteio[1]['freq']}*\n\n"
                f"🍀 *Dica:* Entrada recomendada se ambos forem 80%+"
            )
            send_telegram(msg)
        elif len(dados_escanteio) == 1:
            msg = f"🎫 *BILHETE PARCIAL*\n🎯 {dados_escanteio[0]['mercado']}\n📊 Frequência: {dados_escanteio[0]['freq']}"
            send_telegram(msg)
        else:
            send_telegram("❌ Nenhuma tendência de 10.5 escanteios encontrada para este jogo.")

    except Exception as e:
        send_telegram(f"🚨 Erro: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    minerar_organizado()
