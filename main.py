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

# Mantemos as competições para o bot ir direto nos links se necessário, 
# mas o código abaixo é focado em ler a estrutura que você mandou no print.
COMPETICOES = {
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/",
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
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
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # User-agent para simular o desktop que você está usando no mobile
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Lista de Jogos Detectados (Fuso Brasília)*\n\n"
    
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(6) # Tempo extra para carregar os ícones de áudio/tabela do print
            
            # Scroll agressivo para garantir que o Santos (fim da lista) apareça
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 2000);")
            time.sleep(2)

            # Buscamos todos os elementos de jogos
            jogos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_']")
            secao_adicionada = False
            
            for jogo in jogos:
                try:
                    # Filtro rápido: Se o jogo já começou (tem score live), ignoramos
                    html_content = jogo.get_attribute('innerHTML')
                    if 'event__score--live' in html_content:
                        continue

                    # Extração de Horário
                    texto_completo = jogo.text
                    horario_match = re.search(r'\d{2}:\d{2}', texto_completo)
                    if not horario_match: continue
                    
                    h_utc = horario_match.group()
                    d_match = re.search(r'\d{2}\.\d{2}\.', texto_completo)
                    d_site = d_match.group() if d_match else hoje_str

                    # Trava UTC 2h (Para pegar Palmeiras/Flamengo e ignorar o dia seguinte)
                    if d_site == amanha_str:
                        if int(h_utc.split(':')[0]) >= 2: continue
                    elif d_site != hoje_str:
                        continue

                    # CAPTURA DOS TIMES (Pelo seletor de classe que não falha no seu print)
                    home = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text
                    away = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text

                    if home and away:
                        # Converte para Brasília
                        h_br = (datetime.strptime(h_utc, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                        
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        
                        lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                except:
                    continue
            
            if secao_adicionada:
                lista_final += "\n"
        
        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo agendado encontrado.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
