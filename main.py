import os
import time
import requests
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/"
}

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
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def processar_liga(driver, nome_liga, url):
    driver.get(url)
    time.sleep(7)
    jogos_da_liga = []

    try:
        abas = driver.find_elements(By.CSS_SELECTOR, ".tabs__tab")
        for aba in abas:
            if "PRÓXIMOS" in aba.text.upper():
                driver.execute_script("arguments[0].click();", aba)
                time.sleep(5)
                break
    except: pass

    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
    
    for el in elementos:
        try:
            # Captura os elementos internos para evitar erro de Regex no texto bruto
            h_utc = el.find_element(By.CSS_SELECTOR, ".event__time").text.replace("\n", "").strip()
            t1 = el.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
            t2 = el.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()

            if h_utc and t1 and t2:
                # Conversão de Fuso
                h_obj = datetime.strptime(h_utc, "%H:%M")
                h_br_obj = h_obj - timedelta(hours=3)
                h_br = h_br_obj.strftime("%H:%M")

                # Filtro de horário para garantir que é hoje/noite de hoje
                if h_br_obj.hour >= 11:
                    jogos_da_liga.append(f"🕒 `{h_br}` | *{t1} x {t2}*")
        except: continue
    
    return list(dict.fromkeys(jogos_da_liga))

def main():
    driver = configurar_driver()
    mensagem_final = f"🏆 *LISTA DE HOJE - {datetime.now().strftime('%d/%m')}*\n\n"
    encontrou_algo = False

    try:
        for nome, url in COMPETICOES.items():
            jogos = processar_liga(driver, nome, url)
            if jogos:
                encontrou_algo = True
                mensagem_final += f"--- {nome} ---\n" + "\n".join(jogos) + "\n\n"

        if encontrou_algo:
            enviar_telegram(mensagem_final)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
