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
    # User-agent atualizado para evitar bloqueios
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_teste_completo():
    send_telegram("🚀 *LOG:* Iniciando extração de elite (Filtro por Fração)...")
    browser = configurar_browser()
    url_confronto = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    entradas_escanteio = []

    try:
        # --- LOG 1: ACESSO ---
        browser.get(url_confronto)
        send_telegram(f"✅ *LOG 1:* URL acessada com sucesso:\n`{url_confronto}`")
        
        wait = WebDriverWait(browser, 25)
        
        # --- LOG 2: ABA PARTIDAS ---
        try:
            # Rola a página para garantir que o elemento seja renderizado
            browser.execute_script("window.scrollTo(0, 500);")
            time.sleep(3)
            
            # Tenta clicar na aba "Partidas" onde ficam as tendências H2H
            aba = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#tab:matches"]')))
            browser.execute_script("arguments[0].click();", aba)
            send_telegram("✅ *LOG 2:* Aba 'Partidas' clicada e aberta.")
        except Exception as e:
            send_telegram(f"⚠️ *LOG 2:* Erro ao clicar na aba: {str(e)[:50]}")

        # Aguarda o carregamento interno dos cards (Tendências demoram mais que o placar)
        time.sleep(15)
        
        # --- LOG 3: EXTRAÇÃO ---
        # Buscamos pela classe que contém as linhas de estatísticas
        blocos = browser.find_elements(By.CLASS_NAME, "p_sm")
        
        for b in blocos:
            texto_bloco = b.text.strip()
            
            # FILTRO: Deve conter '/' (indica tendência 10/10) e a palavra 'escanteio'
            if "/" in texto_bloco and "escanteio" in texto_bloco.lower():
                linhas = [l.strip() for l in texto_bloco.split('\n') if l.strip()]
                
                # Se o bloco tiver a estrutura esperada: [Time, Mercado, Fração]
                if len(linhas) >= 3:
                    time_nome = linhas[0]
                    mercado = linhas[1]
                    frequencia = linhas[-1] # A fração é sempre o último elemento
                    
                    # Verifica se o mercado cita 10.5 especificamente
                    if "10.5" in mercado:
                        entradas_escanteio.append(f"🚩 *{time_nome}*\n🔸 {mercado}\n📊 Frequência: *{frequencia}*")

        if entradas_escanteio:
            corpo_final = "\n\n".join(entradas_escanteio)
            send_telegram(f"✅ *LOG 3:* Escanteios encontrados!\n\n{corpo_final}")
        else:
            # Debug: se não achar nada, manda o que ele viu num bloco com "/"
            exemplo = "Nenhum bloco com '/'"
            for b in blocos:
                if "/" in b.text:
                    exemplo = b.text.replace("\n", " | ")
                    break
            send_telegram(f"❌ *LOG 3:* Não isolou 10.5 escanteios.\n*Amostra lida:* `{exemplo}`")

    except Exception as e:
        send_telegram(f"🚨 *ERRO NO PROCESSO:* {str(e)}")
    finally:
        browser.quit()
        send_telegram("🏁 *LOG:* Teste finalizado.")

if __name__ == "__main__":
    executar_teste_completo()
