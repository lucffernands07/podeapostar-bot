import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Voltamos para a página principal que traz todos os jogos
URL_PRINCIPAL = "https://www.flashscore.com.br/"

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,5000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # ESSENCIAL: Forçar o navegador a ser UTC para a trava bater com o horário do site
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    mensagem_final = f"⚽ *TODOS OS JOGOS DE HOJE - {hoje_ref.strftime('%d/%m')}*\n\n"
    contador = 0

    try:
        driver.get(URL_PRINCIPAL)
        time.sleep(10)

        # Na home, os jogos também usam a classe .event__match
        jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")

        for jogo in jogos:
            try:
                # Se já pegamos 50 jogos válidos, paramos
                if contador >= 50: break

                texto_bloco = jogo.text.replace("\n", " ")
                horario_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                
                # Nomes dos times (usando o seletor wcl-name que confirmamos no seu HTML)
                times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                if len(times) < 2: continue
                t1, t2 = times[0].text.strip(), times[1].text.strip()

                # Extração do Horário
                h_utc_solo = horario_raw.split()[-1] 
                h_obj = datetime.strptime(h_utc_solo, "%H:%M")
                h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")

                # --- A MESMA REGRA DE OURO ---
                aceitar = False
                
                # Se tem data de amanhã (ex: 09.04), só aceita se for madrugada UTC (até 3h)
                if amanha_no_site in horario_raw or amanha_no_site in texto_bloco:
                    if h_obj.hour <= 3:
                        aceitar = True
                
                # Se não tem data, aceita se o horário de Brasília for "hoje" (>= 11h)
                elif "." not in horario_raw:
                    h_br_hour = (h_obj - timedelta(hours=3)).hour
                    if h_br_hour >= 11:
                        aceitar = True

                if aceitar:
                    mensagem_final += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                    contador += 1
                    
                    # Envia em blocos de 25 para o Telegram não travar
                    if contador % 25 == 0:
                        enviar_telegram(mensagem_final)
                        mensagem_final = "" # Limpa para o próximo bloco

            except: continue

        # Envia o que sobrar
        if mensagem_final.strip() and contador > 0:
            enviar_telegram(mensagem_final)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
