import os
import time
import requests
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Proteção contra mensagens gigantes
    if len(mensagem) > 4000:
        for i in range(0, len(mensagem), 4000):
            requests.post(url, data={"chat_id": chat_id, "text": mensagem[i:i+4000], "parse_mode": "Markdown"})
    else:
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        # 1. Abre a home (Aba TODOS por padrão)
        driver.get("https://www.flashscore.com.br/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        
        # 2. Scroll para carregar os blocos de elite (Liberta/Sula/Champions)
        for _ in range(4):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)

        jogos_elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        lista_final = "⚽ *Lista Geral de Jogos (Horário de Brasília)*\n\n"
        contagem = 0

        for jogo in jogos_elementos:
            try:
                texto_bruto = jogo.text
                
                # Procura o horário no padrão 00:00
                horario_match = re.search(r'\d{2}:\d{2}', texto_bruto)
                if not horario_match: continue

                # CONVERSÃO: Pega o UTC do servidor e traz para Brasília (-3h)
                h_site = datetime.strptime(horario_match.group(), "%H:%M")
                h_br = (h_site - timedelta(hours=3)).strftime("%H:%M")

                linhas = texto_bruto.split('\n')
                # Filtra nomes de times (mais de 3 letras, ignora termos técnicos)
                termos_off = ['PREVIEW', 'LIVE', 'AO VIVO', 'ENCERRADO', 'FIM', 'INTERVALO']
                nomes = [l for l in linhas if not re.search(r'^\d{1,2}$', l) 
                         and ":" not in l 
                         and l.upper() not in termos_off 
                         and len(l) > 3]

                if len(nomes) >= 2:
                    home, away = nomes[0], nomes[1]
                    lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                    contagem += 1
                
                if contagem >= 50: break
            except:
                continue

        enviar_telegram(lista_final if contagem > 0 else "⚠️ Erro: Nenhum jogo identificado na aba principal.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                
