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

def main():
    driver = configurar_driver()
    hoje_br = datetime.now()
    mensagem_final = f"🏆 *JOGOS DE HOJE - {hoje_br.strftime('%d/%m')}*\n\n"
    encontrou_geral = False

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10)

            # Captura todos os blocos de jogos usando a classe pai que você mandou: event__match
            jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            secao_adicionada = False
            for jogo in jogos:
                try:
                    # 1. Pega o horário (classe event__time no seu HTML)
                    horario_raw = jogo.find_element(By.CSS_SELECTOR, ".event__time").text.split('\n')[0].strip()
                    
                    # 2. Pega os nomes dos times (usando o seletor parcial para as novas classes wcl-name)
                    # Buscamos elementos que contenham 'wcl-name' na classe
                    times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    
                    if len(times) >= 2:
                        t1 = times[0].text.strip()
                        t2 = times[1].text.strip()
                    else:
                        # Backup: tenta pegar pelo 'alt' da imagem se o span falhar
                        logos = jogo.find_elements(By.TAG_NAME, "img")
                        t1 = logos[0].get_attribute("alt").strip()
                        t2 = logos[1].get_attribute("alt").strip()

                    # 3. Lógica de Fuso (UTC -> BR)
                    # Como o GitHub é UTC, 21:30 no seu print aparece como 00:30 do dia seguinte
                    h_obj = datetime.strptime(horario_raw, "%H:%M")
                    h_br_obj = h_obj - timedelta(hours=3)
                    h_br = h_br_obj.strftime("%H:%M")

                    # 4. Filtro de "Hoje": Aceita se for entre 11h e 23h59 de Brasília
                    # Se o texto do bloco tiver a data de amanhã (ex: 09.04), mas for madrugada UTC, é hoje à noite no BR.
                    texto_completo = jogo.text
                    amanha_str = (hoje_br + timedelta(days=1)).strftime("%d.%m.")
                    
                    aceitar = False
                    if amanha_str in texto_completo or "09.04" in texto_completo: # Ajuste manual se precisar
                        if h_obj.hour < 4: aceitar = True 
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
        else:
            print("Nenhum jogo passou pelo filtro.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
