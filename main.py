import os
import requests
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  # <--- ESSA LINHA RESOLVE O ERRO
from webdriver_manager.chrome import ChromeDriverManager

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

def minerar_v_final_corrigida():
    print("🚀 Iniciando minerador...")
    browser = configurar_browser()
    # URL do confronto de teste
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    try:
        browser.get(url_confronto)
        time.sleep(5)
        
        # Abre a aba Partidas para carregar o conteúdo H2H
        try:
            # Usando o By corretamente agora
            aba = browser.find_element(By.CSS_SELECTOR, 'a[href="#tab:matches"]')
            browser.execute_script("arguments[0].click();", aba)
            print("✅ Aba Partidas clicada.")
        except:
            print("⚠️ Aba Partidas não encontrada ou já aberta.")

        # Espera para carregar os dados (15 segundos para garantir)
        time.sleep(15)

        # Capturamos o texto bruto do body
        texto_bruto = browser.find_element(By.TAG_NAME, "body").text
        
        resultados = []
        # Procura por "10.5 escanteios" no texto bruto
        matches = list(re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE))
        
        print(f"🔎 Ocorrências de '10.5 escanteios' encontradas: {len(matches)}")

        for m in matches:
            inicio_busca = m.end()
            # Olhamos os próximos 60 caracteres após a palavra "escanteios"
            trecho_apos = texto_bruto[inicio_busca : inicio_busca + 60]
            
            # Busca a primeira fração (ex: 10/10 ou 8/9) nesse trecho à direita
            frequencia = re.search(r"(\d+/\d+)", trecho_apos)
            
            if frequencia:
                # Descobre se o mercado era "Menos" ou "Mais" olhando o texto imediatamente ANTES
                trecho_antes = texto_bruto[m.start() - 30 : m.start()]
                tipo = "Menos" if "Menos" in trecho_antes else "Mais"
                
                resultados.append({"tipo": tipo, "freq": frequencia.group(1)})

        if len(resultados) >= 2:
            msg = (
                f"🎫 *BILHETE DE ESCANTEIOS FINAL*\n🏟️ Panathinaikos x Real Betis\n\n"
                f"🏠 *CASA*\n🎯 {resultados[0]['tipo']} de 10.5 escanteios\n📊 Frequência: *{resultados[0]['freq']}*\n\n"
                f"🚀 *FORA*\n🎯 {resultados[1]['tipo']} de 10.5 escanteios\n📊 Frequência: *{resultados[1]['freq']}*"
            )
            send_telegram(msg)
            print("✅ Bilhete enviado ao Telegram!")
        else:
            msg_erro = f"❌ Não isolou os dois times. Encontrado: {len(resultados)} dados."
            send_telegram(msg_erro)
            print(msg_erro)

    except Exception as e:
        msg_critico = f"🚨 Erro no processo: {e}"
        send_telegram(msg_critico)
        print(msg_critico)
    finally:
        browser.quit()

if __name__ == "__main__":
    minerar_v_final_corrigida()
