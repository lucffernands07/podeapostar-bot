import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    mensagem_final = f"🏆 *JOGOS DE HOJE - {hoje_ref.strftime('%d/%m')}*\n\n"
    encontrou_geral = False

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            
            try:
                # ESPERA ATÉ 15 SEGUNDOS para os jogos aparecerem na tela
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match"))
                )
                
                jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                secao_adicionada = False

                for jogo in jogos:
                    try:
                        tempo_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                        t1 = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                        t2 = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()

                        # Pega apenas HH:MM
                        horario_utc = tempo_raw.split()[-1]
                        h_obj = datetime.strptime(horario_utc, "%H:%M")
                        h_br_obj = h_obj - timedelta(hours=3)
                        h_br = h_br_obj.strftime("%H:%M")

                        # Lógica da Virada ( Flamengo às 21:30 )
                        amanha_str = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
                        eh_hoje = False
                        
                        if amanha_str in tempo_raw:
                            if h_obj.hour < 4: eh_hoje = True # Madrugada UTC = Noite BR
                        elif "." not in tempo_raw:
                            eh_hoje = True

                        if eh_hoje:
                            if not secao_adicionada:
                                mensagem_final += f"--- {nome_comp} ---\n"
                                secao_adicionada = True
                                encontrou_geral = True
                            mensagem_final += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                    except: continue
                
                if secao_adicionada: mensagem_final += "\n"

            except Exception as e:
                print(f"Tempo esgotado ou erro em {nome_comp}")

        if encontrou_geral:
            enviar_telegram(mensagem_final)
        else:
            print("Nenhum jogo capturado após as verificações.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
