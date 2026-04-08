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
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/",
    "Europa League": "https://www.flashscore.com.br/futebol/europa/liga-europa/"
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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Lista de Jogos Atualizada*\n\n"
    
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(7)
            
            # 1. SCROLL para carregar os Playoffs (que você mandou no HTML)
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)

            # 2. BUSCA AVANÇADA: Procuramos pelo ID g_1_ OU pelo aria-describedby que você mandou
            # Isso garante que mesmo jogos em destaque ou playoffs sejam pegos
            jogos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_'], [aria-describedby^='g_1_']")
            
            secao_adicionada = False
            for jogo in jogos:
                try:
                    texto = jogo.text
                    if ":" not in texto or "ENCERRADO" in texto.upper(): continue

                    # Extração de Horário
                    h_match = re.search(r'(\d{2}:\d{2})', texto)
                    if not h_match: continue
                    h_utc = h_match.group(1)

                    # Filtro de Data / Trava 2h UTC
                    d_match = re.search(r'(\d{2}\.\d{2}\.)', texto)
                    d_site = d_match.group(1) if d_match else hoje_str
                    if d_site == amanha_str and int(h_utc.split(':')[0]) >= 2: continue
                    elif d_site != hoje_str and d_site != amanha_str: continue

                    # Captura dos nomes usando as classes de participantes
                    home = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text
                    away = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text

                    if home and away:
                        h_br = (datetime.strptime(h_utc, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                except: continue
            
            if secao_adicionada: lista_final += "\n"
        
        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo pendente encontrado.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
