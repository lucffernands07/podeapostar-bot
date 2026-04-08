import os
import time
import requests
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

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    # Data de amanhã no formato do site para conferência
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    mensagem_final = f"🏆 *JOGOS DE HOJE - {hoje_ref.strftime('%d/%m')}*\n\n"
    encontrou_geral = False

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10)

            jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            secao_adicionada = False

            for jogo in jogos:
                try:
                    # Captura o texto do bloco para ver se tem a data de amanhã
                    texto_bloco = jogo.text.replace("\n", " ")
                    
                    horario_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    # Se tiver data (ex: 09.04. 02:00), pega só o final
                    h_utc_solo = horario_raw.split()[-1] 
                    
                    times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    t1 = times[0].text.strip()
                    t2 = times[1].text.strip()

                    # Conversão para Brasília
                    h_obj = datetime.strptime(h_utc_solo, "%H:%M")
                    h_br_obj = h_obj - timedelta(hours=3)
                    h_br = h_br_obj.strftime("%H:%M")

                    # --- A REGRA DE OURO ---
                    aceitar = False
                    
                    # 1. Se o jogo está marcado como AMANHÃ no site, mas a hora UTC é madrugada (00h-03h)
                    # Isso significa que é HOJE à noite no Brasil (21h-23h59)
                    if amanha_no_site in horario_raw or amanha_no_site in texto_bloco:
                        if h_obj.hour <= 3: 
                            aceitar = True
                    
                    # 2. Se o jogo está marcado como HOJE (ou sem data), aceitamos se for >= 11h BR
                    # (Para não pegar jogos que já rolaram de manhã cedo no fuso deles)
                    elif h_br_obj.hour >= 11:
                        aceitar = True

                    if aceitar:
                        if not secao_adicionada:
                            mensagem_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                            encontrou_geral = True
                        mensagem_final += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                except: continue
            
            if secao_adicionada: mensagem_final += "\n"

        if encontrou_geral:
            enviar_telegram(mensagem_final)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
