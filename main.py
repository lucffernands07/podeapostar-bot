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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    # Data de referência (Hoje no Brasil: 08/04)
    hoje_br = datetime.now()
    lista_final = f"🏆 *JOGOS DE HOJE - {hoje_br.strftime('%d/%m')} (COMPLETO)*\n\n"
    
    hoje_str = hoje_br.strftime("%d.%m.")
    amanha_str = (hoje_br + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)

            # Força aba PRÓXIMOS
            try:
                driver.execute_script("var a=document.querySelectorAll('.tabs__tab');for(var t of a){if(t.innerText.includes('PRÓXIMOS'))t.click();}")
                time.sleep(5)
            except: pass

            corpo_texto = driver.find_element(By.TAG_NAME, "body").text
            linhas = corpo_texto.split('\n')
            
            secao_adicionada = False
            for i in range(len(linhas)):
                if re.match(r'^\d{2}:\d{2}$', linhas[i]):
                    try:
                        h_utc_str = linhas[i]
                        time1 = linhas[i+1]
                        time2 = linhas[i+2]
                        if "PREVIEW" in time1 or len(time1) < 3: continue

                        # Verifica se existe data explícita perto do horário
                        texto_contexto = " ".join(linhas[max(0, i-3):i])
                        
                        # LOGICA DO FUSO: 
                        # Se o site diz que é AMANHÃ, mas a hora UTC é menor que 03:00,
                        # significa que no Brasil ainda é HOJE à noite.
                        hora_h = int(h_utc_str.split(':')[0])
                        
                        eh_hoje = False
                        if amanha_str in texto_contexto:
                            if hora_h < 3: eh_hoje = True # Jogos das 21h, 22h, 23h do Brasil
                        elif hoje_str in texto_contexto or re.search(r'\d{2}:\d{2}', h_utc_str):
                            # Se não achou "amanhã", e a hora faz sentido, assume hoje
                            if not (hoje_str not in texto_contexto and hora_h < 10): # Evita pegar jogos da manhã seguinte
                                eh_hoje = True

                        if eh_hoje:
                            h_br = (datetime.strptime(h_utc_str, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                            if not secao_adicionada:
                                lista_final += f"--- {nome_comp} ---\n"
                                secao_adicionada = True
                            lista_final += f"🕒 `{h_br}` | *{time1} x {time2}*\n"
                    except: continue
            
            if secao_adicionada: lista_final += "\n"

        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo capturado. Verifique o log.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
