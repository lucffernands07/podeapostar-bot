import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Foco no link que você mandou
URL_TESTE = "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/"

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

def main():
    driver = configurar_driver()
    mensagem = "🏆 *TESTE LIBERTADORES - JOGOS DE HOJE*\n\n"
    encontrou = False

    try:
        driver.get(URL_TESTE)
        time.sleep(8)

        # O Flashscore agrupa os jogos de hoje em blocos com a classe .event__match
        jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")

        for jogo in jogos:
            try:
                # Captura os dados exatamente como aparecem nos campos da página
                # Seletor de tempo (ex: 19:00 ou 09.04. 00:30)
                tempo_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                
                # Seletor dos nomes dos times
                t1 = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                t2 = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()

                # Pega apenas o horário (HH:MM) ignorando a data se houver
                horario_utc = tempo_raw.split()[-1] 
                
                # Conversão: UTC para Brasília (-3h)
                h_obj = datetime.strptime(horario_utc, "%H:%M")
                h_br_obj = h_obj - timedelta(hours=3)
                h_br = h_br_obj.strftime("%H:%M")

                # LÓGICA DE FILTRO: 
                # Se no texto do bloco tem a data de AMANHÃ (ex: 09.04), 
                # só aceitamos se for madrugada no UTC (00h às 03h), 
                # pois isso significa que no Brasil ainda é a noite de hoje (21h às 00h).
                
                amanha_str = (datetime.now() + timedelta(days=1)).strftime("%d.%m.")
                
                eh_hoje = False
                if amanha_str in tempo_raw:
                    if h_obj.hour < 4: # Jogos da noite de hoje
                        eh_hoje = True
                elif "." not in tempo_raw: # Se não tem data, o site considera que é hoje
                    eh_hoje = True

                if eh_hoje:
                    mensagem += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                    encontrou = True

            except Exception as e:
                continue

        if encontrou:
            enviar_telegram(mensagem)
        else:
            print("Nenhum jogo de hoje encontrado no link.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
