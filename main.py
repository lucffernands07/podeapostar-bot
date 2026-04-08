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
    # Forçamos o navegador a operar em UTC (Londres) para o site não esconder nada da virada do dia
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def processar_liga(driver, nome_liga, url):
    driver.get(url)
    time.sleep(8)
    jogos_extraidos = []
    
    # 1. Força a aba PRÓXIMOS
    try:
        driver.execute_script("var a=document.querySelectorAll('.tabs__tab');for(var t of a){if(t.innerText.includes('PRÓXIMOS'))t.click();}")
        time.sleep(5)
    except: pass

    # 2. Captura por seletores específicos para evitar o "x -" no final
    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
    
    for el in elementos:
        try:
            # Pegamos o horário que está em UTC no site
            h_utc_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
            t1 = el.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
            t2 = el.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()

            # CONVERSÃO: O robô pegou 00:30 (UTC)? Subtraímos 3h para virar 21:30 (Brasília)
            h_obj = datetime.strptime(h_utc_raw, "%H:%M")
            h_br_obj = h_obj - timedelta(hours=3)
            h_br = h_br_obj.strftime("%H:%M")

            # FILTRO INTELIGENTE:
            # Queremos jogos que acontecem HOJE no Brasil (das 12:00 até 23:59).
            # Como estamos em UTC, o site vai mostrar jogos de 15:00 UTC até as 02:59 UTC do "dia seguinte".
            # Todos esses, ao subtrair 3h, caem no nosso "hoje".
            
            hora_br_int = h_br_obj.hour
            
            # Se for Champions e o horário for 16h, mas for de "amanhã" no fuso deles,
            # a gente filtra pela aba ou pelo contexto do texto se necessário.
            # Mas a regra da hora mata 90% dos erros:
            if hora_br_int >= 11:
                # Trava para não pegar a rodada de amanhã da Champions (que seria 16h BR também)
                # No UTC, o jogo de amanhã às 16h seria 19h UTC. 
                # Se o bot estiver lendo a aba "Próximos" e ver um jogo de 19h UTC que já é dia 09/04,
                # precisamos conferir se o elemento tem alguma marcação de data.
                texto_completo = el.text
                if "09.04." in texto_completo or "amanhã" in texto_completo.lower():
                    # Só aceita se for madrugada (00h às 02h UTC), que é o nosso 21h-23h.
                    if h_obj.hour >= 3: 
                        continue

                jogos_extraidos.append(f"🕒 `{h_br}` | *{t1} x {t2}*")
        except: continue
    
    return list(dict.fromkeys(jogos_extraidos))

def main():
    driver = configurar_driver()
    hoje_formatado = datetime.now().strftime('%d/%m')
    mensagem_final = f"🏆 *JOGOS DE HOJE - {hoje_formatado} (MÉTODO UTC)*\n\n"
    encontrou_algo = False

    try:
        for nome, url in COMPETICOES.items():
            print(f"Buscando {nome} em UTC...")
            jogos = processar_liga(driver, nome, url)
            
            if jogos:
                encontrou_algo = True
                mensagem_final += f"--- {nome} ---\n" + "\n".join(jogos) + "\n\n"

        if encontrou_algo:
            enviar_telegram(mensagem_final)
        else:
            print("Nada encontrado.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
