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
    # Dividir a mensagem se ela for muito grande para o Telegram (limite de 4096 caracteres)
    if len(mensagem) > 4000:
        partes = [mensagem[i:i+4000] for i in range(0, len(mensagem), 4000)]
        for parte in partes:
            requests.post(url, data={"chat_id": chat_id, "text": parte, "parse_mode": "Markdown"})
    else:
        payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=payload)

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        print("Acessando site para colher jogos de hoje...")
        driver.get("https://www.flashscore.com.br/")
        
        # Espera inicial para carregar a estrutura
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        
        # Rolar a página algumas vezes para carregar campeonatos de baixo (Liberta, Sula)
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)

        jogos_elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        lista_final = f"🏆 *Lista de Jogos de Hoje ({len(jogos_elementos)} encontrados)*\n\n"
        contagem = 0

        for jogo in jogos_elementos:
            try:
                texto_bruto = jogo.text
                dados = texto_bruto.split('\n')
                
                # Regra: Geralmente o horário contém ":" e é o primeiro elemento
                if dados and ":" in dados[0]:
                    horario = dados[0]
                    # Identifica mandante e visitante ignorando ícones de cards ou placares
                    # Em jogos não começados, o formato costuma ser [Horário, Mandante, Visitante]
                    home = dados[1]
                    away = dados[2] if len(dados) >= 3 else "A definir"
                    
                    # Limpeza simples para remover lixo de texto
                    if "Encerrado" not in texto_bruto and "Adiado" not in texto_bruto:
                        lista_final += f"🕒 `{horario}` | *{home} x {away}*\n"
                        contagem += 1
                
                # NOVO LIMITE: 50 JOGOS
                if contagem >= 50: 
                    break 
            except:
                continue

        if contagem > 0:
            enviar_telegram(lista_final)
            print(f"Sucesso! {contagem} jogos enviados.")
        else:
            enviar_telegram("⚠️ Nenhum jogo agendado encontrado na varredura.")

    except Exception as e:
        enviar_telegram(f"❌ Erro crítico: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
