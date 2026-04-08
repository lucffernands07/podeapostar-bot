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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # FORÇA O NAVEGADOR A OPERAR EM UTC (LONDRES)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    
    # Formato exato que o Flashscore usa para data (ex: 09.04.)
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    mensagem_final = f"🏆 *JOGOS DE HOJE - {hoje_ref.strftime('%d/%m')}*\n\n"
    encontrou_geral = False

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10) # Tempo para carregar os scripts do Flashscore

            jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            secao_adicionada = False

            for jogo in jogos:
                try:
                    # Captura o texto do bloco para análise de data e horário
                    texto_bloco = jogo.text.replace("\n", " ")
                    horario_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    
                    # Seletores dinâmicos baseados no seu HTML (wcl-name)
                    times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    if len(times) < 2: continue
                    t1, t2 = times[0].text.strip(), times[1].text.strip()

                    # Pega apenas o horário HH:MM (ignora a data se houver no campo)
                    h_utc_solo = horario_raw.split()[-1] 
                    h_obj = datetime.strptime(h_utc_solo, "%H:%M")
                    
                    # Conversão para exibição no Brasil (UTC - 3)
                    h_br_obj = h_obj - timedelta(hours=3)
                    h_br = h_br_obj.strftime("%H:%M")

                    # --- A REGRA DE OURO BLINDADA ---
                    aceitar = False
                    
                    # 1. Se o bloco contém a data de amanhã (ex: 09.04.)
                    if amanha_no_site in horario_raw or amanha_no_site in texto_bloco:
                        # SÓ ACEITA se o horário em Londres for madrugada (00h até 03h)
                        # Isso significa que no Brasil o jogo é HOJE entre 21h e 00h.
                        if h_obj.hour <= 3:
                            aceitar = True
                        else:
                            # É jogo de amanhã à noite (ex: Corinthians 21h). DESCARTA.
                            aceitar = False
                    
                    # 2. Se NÃO tem a data de amanhã, aceita se a hora BR for de hoje (>= 11h)
                    elif "." not in horario_raw:
                        if h_br_obj.hour >= 11:
                            aceitar = True

                    if aceitar:
                        if not secao_adicionada:
                            mensagem_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                            encontrou_geral = True
                        mensagem_final += f"🕒 `{h_br}` | *{t1} x {t2}*\n"
                        
                except Exception as e:
                    continue
            
            if secao_adicionada:
                mensagem_final += "\n"

        if encontrou_geral:
            enviar_telegram(mensagem_final)
        else:
            print("Nenhum jogo encontrado para os critérios de hoje.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
