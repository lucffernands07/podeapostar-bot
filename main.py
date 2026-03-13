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

def minerar_preciso():
    browser = configurar_browser()
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    lista_escanteios = []

    try:
        browser.get(url_confronto)
        wait = WebDriverWait(browser, 20)
        
        # Abre a aba Partidas
        try:
            browser.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            aba = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba)
        except: pass

        time.sleep(15)

        # Captura todos os blocos de estatística
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        
        for b in blocos:
            texto = b.text.strip()
            
            # FILTRO CRUCIAL: Só entra se a palavra 'escanteio' estiver no bloco
            if "escanteio" in texto.lower():
                linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                
                # Procura a fração (ex: 10/10) dentro deste bloco específico
                for linha in linhas:
                    if "/" in linha:
                        mercado = "Menos de 10.5" if "Menos" in texto else "Mais de 10.5"
                        lista_escanteios.append({"mercado": mercado, "freq": linha})
                        break 

        # Montagem baseada na sua observação: 1º é Casa, 2º é Visitante
        if len(lista_escanteios) >= 2:
            casa = lista_escanteios[0]
            fora = lista_escanteios[1]
            
            msg = (
                f"🎫 *BILHETE DE ESCANTEIOS*\n🏟️ Panathinaikos x Real Betis\n\n"
                f"🏠 *CASA (Panathinaikos)*\n🎯 {casa['mercado']}\n📊 Frequência: *{casa['freq']}*\n\n"
                f"🚀 *FORA (Real Betis)*\n🎯 {fora['mercado']}\n📊 Frequência: *{fora['freq']}*\n\n"
                f"✅ *Filtro aplicado:* Ignorado 6/7 de gols/cartões."
            )
            send_telegram(msg)
        else:
            send_telegram(f"⚠️ Encontrado apenas {len(lista_escanteios)} dado de escanteio. Verifique se o mercado 10.5 está aberto para ambos.")

    except Exception as e:
        send_telegram(f"🚨 Erro: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    minerar_preciso()
            
