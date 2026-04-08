import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Importante para sites que detectam automação
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Acessa a página de jogos agendados (Próximos)
        driver.get("https://www.flashscore.com.br/")
        
        # 2. Aguarda o botão de data aparecer e tenta selecionar (opcional para teste)
        # Se você quiser apenas os jogos que já estão na tela, pule esta parte.
        try:
            botao_data = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="wcl-dayPickerButton"]')))
            print(f"Data atual no site: {botao_data.text}")
        except:
            print("Botão de data não encontrado, seguindo com a página padrão...")

        # 3. Localiza os blocos de jogos
        # O Flashscore agrupa por 'event__header' (campeonato) e 'event__match' (jogo)
        time.sleep(5) # Garantia para renderização do JS
        
        eventos = driver.find_elements(By.CSS_SELECTOR, '.leagues--live .event__match, .leagues--static .event__match')
        
        # Seletor baseado no seu snippet para o link do jogo
        links_jogos = driver.find_elements(By.CSS_SELECTOR, 'a.eventRowLink')
        
        lista_jogos = "⚽ *Lista de Jogos Extraída*\n\n"
        
        if not links_jogos:
            lista_jogos += "Nenhum jogo encontrado no momento."
        else:
            for i, link in enumerate(links_jogos[:15]): # Pega os 15 primeiros para teste
                # O título do link no Flashscore geralmente contém os times
                info = link.get_attribute('title') or "Jogo sem título"
                url_jogo = link.get_attribute('href')
                lista_jogos += f"• {info}\n"

        enviar_telegram(lista_jogos)

    except Exception as e:
        enviar_telegram(f"❌ Erro ao processar: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
        
