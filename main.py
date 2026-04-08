import os
import time
import requests
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless") # Se continuar dando erro, comente esta linha para ver o que acontece
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 20)
    lista_final = "🏆 *Lista Final (Força Bruta)*\n\n"
    
    # Referências de Data
    hoje_utc = datetime.now()
    amanha_utc = hoje_utc + timedelta(days=1)
    datas_alvo = [hoje_utc.strftime("%d.%m."), amanha_utc.strftime("%d.%m.")]

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            
            # Espera até que QUALQUER jogo apareça na tela
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='g_1_']")))
            except:
                continue # Se não achou nada em 20s, pula pra próxima liga

            # Scroll para garantir carregamento total
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)

            jogos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_']")
            secao_adicionada = False
            
            for jogo in jogos:
                try:
                    # Pega o texto e verifica se tem horário
                    texto = jogo.text
                    if ":" not in texto: continue
                    
                    # Filtro de AO VIVO (mais simples)
                    if "AO VIVO" in texto.upper() or "LIVE" in texto.upper():
                        continue

                    # Horário e Data
                    h_match = re.search(r'(\d{2}:\d{2})', texto)
                    if not h_match: continue
                    h_utc_str = h_match.group(1)
                    
                    d_match = re.search(r'(\d{2}\.\d{2}\.)', texto)
                    d_site = d_match.group(1) if d_match else datas_alvo[0]

                    # Trava das 2h UTC (Se for amanhã e > 02:00, pula)
                    if d_site == datas_alvo[1]:
                        if int(h_utc_str.split(':')[0]) >= 2: continue
                    elif d_site not in datas_alvo:
                        continue

                    # Nomes dos times (usando as classes que não falham)
                    home = jogo.find_element(By.CLASS_NAME, "event__participant--home").text
                    away = jogo.find_element(By.CLASS_NAME, "event__participant--away").text

                    if home and away:
                        # Converte fuso
                        h_obj = datetime.strptime(h_utc_str, "%H:%M")
                        h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                        
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        
                        lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                except:
                    continue
            
            if secao_adicionada:
                lista_final += "\n"
        
        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Falha crítica: Nenhum jogo capturado.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
