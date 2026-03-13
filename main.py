import os
import requests
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

def minerar_v_final():
    browser = configurar_browser()
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    try:
        browser.get(url_confronto)
        time.sleep(5)
        
        # Abre a aba Partidas para carregar o JSON interno
        try:
            aba = browser.find_element(By.CSS_SELECTOR, 'a[href="#tab:matches"]')
            browser.execute_script("arguments[0].click();", aba)
        except: pass

        # Espera generosa para garantir que o texto "10/10" apareça no corpo da página
        time.sleep(15)

        # Capturamos o texto bruto exatamente como você me mandou no LOG anterior
        texto_bruto = browser.find_element(By.TAG_NAME, "body").text
        
        # LÓGICA DE EXTRAÇÃO À DIREITA:
        # Procuramos por "10.5 escanteios" e pegamos a FRAÇÃO mais próxima que vem DEPOIS dele.
        
        # Vamos usar uma expressão regular que diz: 
        # "Ache '10.5 escanteios', pule o lixo, e pegue a primeira fração (nn/nn)"
        resultados = []
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        for m in matches:
            inicio_busca = m.end()
            # Olhamos os próximos 50 caracteres após a palavra "escanteios"
            trecho_apos = texto_bruto[inicio_busca : inicio_busca + 50]
            
            # Busca a primeira fração (ex: 10/10 ou 8/9) nesse trecho
            frequencia = re.search(r"(\d+/\d+)", trecho_apos)
            
            if frequencia:
                # Descobre se o mercado era "Menos" ou "Mais" olhando o texto antes
                trecho_antes = texto_bruto[m.start() - 20 : m.start()]
                tipo = "Menos" if "Menos" in trecho_antes else "Mais"
                
                resultados.append({"tipo": tipo, "freq": frequencia.group(1)})

        if len(resultados) >= 2:
            msg = (
                f"🎫 *BILHETE DE ESCANTEIOS FINAL*\n🏟️ Panathinaikos x Real Betis\n\n"
                f"🏠 *CASA*\n🎯 {resultados[0]['tipo']} de 10.5 escanteios\n📊 Frequência: *{resultados[0]['freq']}*\n\n"
                f"🚀 *FORA*\n🎯 {resultados[1]['tipo']} de 10.5 escanteios\n📊 Frequência: *{resultados[1]['freq']}*"
            )
            send_telegram(msg)
        else:
            send_telegram(f"⚠️ Encontrado apenas: {resultados}. O JSON pode ter mudado.")

    except Exception as e:
        send_telegram(f"🚨 Erro: {e}")
    finally:
        browser.quit()

if __name__ == "__main__":
    minerar_v_final()
                
