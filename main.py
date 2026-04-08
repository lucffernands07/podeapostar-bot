import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id:
        print("Erro: Variáveis de ambiente do Telegram não configuradas.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # O WebDriver Manager baixa o driver correto automaticamente no GitHub Actions
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main():
    driver = configurar_driver()
    try:
        print("Iniciando busca de dados...")
        # Exemplo de navegação
        driver.get("https://www.google.com") 
        
        # Lógica de scraping aqui
        # Exemplo: Encontrar jogos que batem com seu critério de 5/5 ou 4/5
        
        resultado_fake = "⚽ *Bot de Apostas*\n\nProcessamento concluído com sucesso no servidor!"
        enviar_telegram(resultado_fake)
        
    except Exception as e:
        enviar_telegram(f"❌ Erro na execução: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
