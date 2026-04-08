import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

URL_LIBERTADORES = "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/"

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    msg = "🔍 **LOG DE MAPEAMENTO - LIBERTADORES**\n\n"
    jogos_encontrados = []
    
    try:
        driver.get(URL_LIBERTADORES)
        time.sleep(12) 
        
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        if not elementos:
            msg += "⚠️ Nenhum elemento de jogo encontrado na página."
        else:
            for el in elementos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_utc_str = tempo_raw.split()[-1]
                    h_obj = datetime.strptime(h_utc_str, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    t1, t2 = times[0].text.strip(), times[1].text.strip()
                    
                    # Logica da Trava UTC
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 11: aceitar = True

                    status_icon = "✅" if aceitar else "❌"
                    jogos_encontrados.append(f"{status_icon} `{h_br}` | {t1} x {t2} (Site: {tempo_raw})")
                except:
                    continue

        if jogos_encontrados:
            msg += "\n".join(jogos_encontrados)
            msg += f"\n\n📊 Total mapeado: {len(jogos_encontrados)}"
        
        enviar_telegram(msg)
        print("Log enviado. Aguardando confirmação do Luciano.")

    except Exception as e:
        enviar_telegram(f"❌ **ERRO NA ETAPA 1:**\n{str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                    
