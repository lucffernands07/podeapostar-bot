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

def extrair_dados_brutos():
    browser = configurar_browser()
    # Usando o link do Panathinaikos que você passou
    url_alvo = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    status_json = "❌ Não extraído"
    mercado_detectado = "❌ Nenhum"

    try:
        browser.get(url_alvo)
        
        # Em vez de clicar, vamos pegar todo o código fonte da página
        html_completo = browser.page_source
        
        # O segredo: O Sofascore geralmente guarda os dados em um script chamado 'NEXT_DATA' ou 'initialProps'
        # Vamos buscar por padrões de texto de escanteio diretamente no código-fonte bruto (JSON-like)
        print("🔍 Analisando código bruto em busca de padrões de escanteio...")
        
        # Regex para buscar a frase de escanteios no meio do código
        padrão = r'([Mm]enos|[Mm]ais)\s+do\s+que\s+10\.5\s+escanteios\s+\d+/\d+'
        resultado = re.findall(padrão, html_completo, re.IGNORECASE)
        
        # Se o regex simples não achar, procuramos a estrutura de "trends"
        if not resultado:
            # Busca manual por palavras chave próximas
            if "10.5" in html_completo and "escanteio" in html_completo:
                status_json = "✅ Palavras-chave encontradas no código"
                # Tenta isolar o trecho
                pos = html_completo.find("10.5")
                trecho = html_completo[pos-50:pos+50]
                mercado_detectado = f"Trecho: {trecho}"
            else:
                status_json = "❌ Nem no código bruto apareceu"
        else:
            status_json = "✅ Padrão detectado via Regex!"
            mercado_detectado = resultado[0]

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    finally:
        browser.quit()

    # Relatório
    msg = (
        "💎 *EXTRAÇÃO DE DADOS BRUTOS*\n\n"
        f"📊 *Status:* {status_json}\n"
        f"🎯 *Captura:* `{mercado_detectado}`"
    )
    
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    extrair_dados_brutos()
            
