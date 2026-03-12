import os
import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extrair_vencendo_sofascore():
    browser = configurar_browser()
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    mercado_final = "❌ Não isolado"

    try:
        browser.get(url_alvo)
        # Dá um tempo para o JSON interno carregar
        import time
        time.sleep(10)
        
        # O Sofascore guarda TUDO nesse script aqui:
        html = browser.page_source
        
        # 1. Tenta buscar a frase limpa (caso ela esteja renderizada)
        busca_limpa = re.findall(r'([^">]+10\.5\s+escanteios[^"<]+)', html, re.IGNORECASE)
        
        if busca_limpa:
            # Pega a frase que contém os números (ex: 10/10 ou 5/5)
            for frase in busca_limpa:
                if "/" in frase:
                    mercado_final = frase.strip()
                    break
        
        # 2. Se não achou a frase limpa, busca no JSON bruto
        if mercado_final == "❌ Não isolado":
            # Busca por padrões como "less than 10.5 corners" ou "Menos de 10.5"
            # O Sofascore costuma usar chaves como "subtitle" ou "title" no JSON
            match = re.search(r'"(Menos|Mais|Less|More)[^"]+10\.5[^"]+escanteios[^"]+"', html, re.IGNORECASE)
            if match:
                mercado_final = match.group(0).replace('"', '')

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        browser.quit()

    # Relatório
    msg = (
        "🎯 *RESULTADO DA MINERAÇÃO*\n\n"
        f"📊 *Mercado:* `{mercado_final}`\n"
        "---"
    )
    
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    extrair_vencendo_sofascore()
        
