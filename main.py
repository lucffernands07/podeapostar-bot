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
    if not token or not chat_id:
        print("Erro: Variáveis de ambiente não encontradas.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro ao enviar: {e}")

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Evita ser bloqueado como robô
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 25)
    
    try:
        print("Acessando Flashscore...")
        driver.get("https://www.flashscore.com.br/")
        
        # 1. Aguarda e clica na aba 'PRÓXIMOS' para filtrar jogos que ainda não começaram
        try:
            aba_proximos = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filters__tab')]//div[contains(text(), 'PRÓXIMOS')]")))
            driver.execute_script("arguments[0].click();", aba_proximos)
            time.sleep(3)
        except:
            print("Não foi possível clicar na aba 'Próximos', tentando extração direta...")

        # 2. Aguarda a presença dos containers de jogos
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        
        jogos_elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        lista_final = "⚽ *Jogos de Hoje (Lista Atualizada):*\n\n"
        
        contagem = 0
        for jogo in jogos_elementos:
            try:
                # Extração dos dados de cada linha
                horario = jogo.find_element(By.CSS_SELECTOR, ".event__time").text
                home = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text
                away = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text
                
                # Limpa horários que podem vir com 'Encerrado' ou 'Adiado'
                if ":" in horario:
                    lista_final += f"🕒 `{horario}` | *{home} x {away}*\n"
                    contagem += 1
                
                # Limite de 30 jogos para não estourar o limite do Telegram em um único envio
                if contagem >= 30: break
            except:
                continue

        if contagem > 0:
            enviar_telegram(lista_final)
        else:
            enviar_telegram("⚠️ Nenhum jogo agendado encontrado para agora.")

    except Exception as e:
        print(f"Erro: {e}")
        enviar_telegram(f"❌ Erro na extração: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
