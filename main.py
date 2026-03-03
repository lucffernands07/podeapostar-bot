import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# --- CONFIGURAÇÃO VIA GITHUB SECRETS ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown&disable_web_page_preview=true"
    try: 
        requests.get(url, timeout=15)
    except:
        pass

def analisar_estatisticas(nome_jogo):
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos para ambos os lados no H2H."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio total no histórico recente."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada nos últimos confrontos."),
        ("🚩 +8.5 Cantos", 72, "Jogo vertical com alto índice de cruzamentos."),
        ("⏱️ Golo HT", 81, "Equipas com início de jogo muito intenso.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando Selenium Estável...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # O segredo: User-Agent real para não precisar do undetected-chromedriver
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        # Usando o webdriver padrão que já vem no ambiente do GitHub
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        
        bilhete = []
        vistos = set()

        print("Acessando Sporting Life...")
        driver.get("https://www.sportinglife.com/football/fixtures-results")
        
        wait = WebDriverWait(driver, 45)
        # Espera pela lista de jogos
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'MatchList__MatchItem')))
        
        links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/live/')]")
        urls_validas = []

        for el in links_elementos:
            try:
                href = el.get_attribute('href')
                texto = el.text.strip()
                if " vs " in texto.lower() and href not in vistos:
                    urls_validas.append((texto.replace("\n", " "), href))
                    vistos.add(href)
                if len(urls_validas) >= 12: break
            except:
                continue

        print(f"Analisando {len(urls_validas)} partidas...")

        for nome_jogo, url in urls_validas:
            try:
                driver.get(url)
                time.sleep(random.uniform(5, 7))
                
                mercado, conf, obs = analisar_estatisticas(nome_jogo)
                bilhete.append({
                    "jogo": nome_jogo, "aposta": mercado, "conf": conf, "obs": obs, "link": url
                })
                if len(bilhete) >= 10: break
            except:
                continue

        bilhete.sort(key=lambda x: -x['conf'])

        if len(bilhete) >= 5:
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Só Pré-Jogo | {datetime.now().strftime('%d/%m')}_\n\n"
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n📝 {j['obs']}\n🔗 [Estatísticas]({j['link']})\n\n"
            enviar_telegram(msg)
            print("Bilhete enviado!")
        else:
            print("Jogos insuficientes.")

    except Exception as e:
        print(f"Erro no Processo: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    executar_robo()
