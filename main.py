import os
import time
import requests
import re
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
    
    # Divide a mensagem se ultrapassar o limite do Telegram
    if len(mensagem) > 4000:
        partes = [mensagem[i:i+4000] for i in range(0, len(mensagem), 4000)]
        for parte in partes:
            requests.post(url, data={"chat_id": chat_id, "text": parte, "parse_mode": "Markdown"})
    else:
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Tenta simular um navegador real para evitar bloqueios e fuso errado
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get("https://www.flashscore.com.br/")
        
        # Espera o carregamento básico
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        
        # Scroll para carregar os jogos "abaixo da dobra" (Liberta/Sula)
        for _ in range(4):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1.5)

        jogos_elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        lista_final = f"🏆 *Jogos de Hoje (Limite: 50)*\n\n"
        contagem = 0

        for jogo in jogos_elementos:
            try:
                texto_bruto = jogo.text
                linhas = texto_bruto.split('\n')
                
                # Busca horário em qualquer uma das primeiras 3 linhas do bloco do jogo
                horario = None
                for linha in linhas[:3]:
                    if re.search(r'\d{2}:\d{2}', linha):
                        horario = re.search(r'\d{2}:\d{2}', linha).group()
                        break
                
                if horario:
                    # Limpa a lista de linhas para achar os nomes dos times
                    # Remove horários, ícones de 'PREVIEW', 'LIVE' e placares se houver
                    dados_limpos = [l for l in linhas if not re.search(r'\d{2}:\d{2}', l) and l not in ['PREVIEW', 'LIVE', 'AO VIVO']]
                    
                    if len(dados_limpos) >= 2:
                        home = dados_limpos[0]
                        away = dados_limpos[1]
                        
                        # Ignora jogos que já estão rolando (com placar) ou encerrados
                        if "Encerrado" not in texto_bruto and "Intervalo" not in texto_bruto:
                            lista_final += f"🕒 `{horario}` | *{home} x {away}*\n"
                            contagem += 1
                
                if contagem >= 50: 
                    break 
            except:
                continue

        if contagem > 0:
            enviar_telegram(lista_final)
        else:
            enviar_telegram("⚠️ Nenhum jogo agendado encontrado com o novo filtro.")

    except Exception as e:
        enviar_telegram(f"❌ Erro: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
