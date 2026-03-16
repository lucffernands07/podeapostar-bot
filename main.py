import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def buscar_id_sofascore(driver, time_casa, time_fora):
    print(f"🔍 Buscando jogo: {time_casa} x {time_fora}...")
    driver.get("https://www.sofascore.com/pt/")
    wait = WebDriverWait(driver, 20)
    
    try:
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        search_input.send_keys(f"{time_casa} {time_fora}")
        time.sleep(5)
        
        # Seleciona o link do jogo nos resultados
        resultado = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(., '{time_casa}') and contains(., '{time_fora}')]/ancestor::a[contains(@href, '/football/match/')]")))
        return resultado.get_attribute("href")
    except:
        return None

def extrair_estatisticas(driver, url_jogo):
    url_limpa = url_jogo.split('#')[0]
    driver.get(url_limpa)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Clica na aba Partidas
        aba = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'tab:matches')] | //div[text()='Partidas']")))
        driver.execute_script("arguments[0].click();", aba)
        
        time.sleep(3)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(6)
        
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # Usamos um dicionário para evitar duplicatas de frações idênticas no mesmo bloco
        encontrados = []
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        for m in matches:
            trecho = texto_bruto[m.end() : m.end() + 50]
            frequencia = re.search(r"(\d+)/(\d+)", trecho)
            if frequencia:
                fracao = f"{frequencia.group(1)}/{frequencia.group(2)}"
                if fracao not in encontrados:
                    encontrados.append(fracao)
        
        return encontrados
    except:
        return []

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def executar_bot():
    driver = configurar_browser()
    # Exemplo com o jogo que validamos
    time_casa, time_fora = "Lazio", "Milan"
    
    url = buscar_id_sofascore(driver, time_casa, time_fora)
    
    if url:
        frações = extrair_estatisticas(driver, url)
        
        if len(frações) >= 2:
            f1_num, f1_den = map(int, frações[0].split('/'))
            f2_num, f2_den = map(int, frações[1].split('/'))
            
            p1 = (f1_num / f1_den) * 100
            p2 = (f2_num / f2_den) * 100
            media = (p1 + p2) / 2
            
            msg = f"🏟️ *{time_casa} x {time_fora}*\n"
            msg += f"🚩 Escanteios < 10.5\n"
            msg += f"🏠 Casa: {frações[0]} ({p1:.1f}%)\n"
            msg += f"🚌 Fora: {frações[1]} ({p2:.1f}%)\n"
            msg += f"📊 Média: {media:.1f}%\n\n"
            
            if p1 >= 90 and p2 >= 90:
                msg += "🔥 *PALPITE: PRIORITÁRIO*"
            elif media >= 85:
                msg += "✅ *PALPITE: APROVADO*"
            
            enviar_telegram(msg)
            print("✅ Relatório enviado ao Telegram!")
        else:
            print("❌ Não foi possível encontrar as duas frações.")
    else:
        print("❌ Jogo não encontrado.")
    
    driver.quit()

if __name__ == "__main__":
    executar_bot()
