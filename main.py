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

# Defina aqui os links das competições que você não pode perder
COMPETICOES = {
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/",
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Fragmenta se for muito grande
    for i in range(0, len(mensagem), 4000):
        requests.post(url, data={"chat_id": chat_id, "text": mensagem[i:i+4000], "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Jogos Monitorados (Fuso Brasília)*\n\n"
    
    try:
        for nome, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(3) # Espera carregar a página da competição
            
            # Pega todos os jogos da página usando o ID global 'g_1_'
            elementos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_']")
            
            lista_final += f"--- {nome} ---\n"
            contagem_comp = 0
            
            for jogo in elementos:
                try:
                    texto = jogo.text
                    horario_match = re.search(r'\d{2}:\d{2}', texto)
                    if not horario_match: continue
                    
                    # Correção de Fuso: Hora do site - 3h
                    h_site = datetime.strptime(horario_match.group(), "%H:%M")
                    h_br = (h_site - timedelta(hours=3)).strftime("%H:%M")
                    
                    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                    termos_off = ['PREVIEW', 'LIVE', 'AO VIVO', 'ENCERRADO', 'INTERVALO', 'FIM']
                    nomes = [l for l in linhas if l.upper() not in termos_off and not re.search(r'^\d{1,2}$', l) and ":" not in l]
                    
                    if len(nomes) >= 2:
                        lista_final += f"🕒 `{h_br}` | *{nomes[0]} x {nomes[1]}*\n"
                        contagem_comp += 1
                except: continue
            
            lista_final += "\n"
            if contagem_comp == 0: lista_final += "⚠️ Nenhum jogo hoje.\n\n"
        
        enviar_telegram(lista_final)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
