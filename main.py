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

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    if len(mensagem) > 4000:
        for i in range(0, len(mensagem), 4000):
            requests.post(url, data={"chat_id": chat_id, "text": mensagem[i:i+4000], "parse_mode": "Markdown"})
    else:
        requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 30)
    
    # Datas de referência
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        driver.get("https://www.flashscore.com.br/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        
        # Scroll para carregar a página inteira
        for _ in range(6):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)

        jogos_elementos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_']")
        lista_final = "🏆 *Jogos de Hoje (Filtro UTC 2h - Aba Todos)*\n\n"
        contagem = 0

        for jogo in jogos_elementos:
            try:
                texto_bruto = jogo.text
                
                # 1. Ignora jogos que já começaram/terminaram
                termos_off = ['LIVE', 'AO VIVO', 'INTERVALO', 'FIM', 'ENCERRADO', 'ADIADO']
                if any(x in texto_bruto.upper() for x in termos_off):
                    continue

                # 2. Captura Horário e Data
                horario_match = re.search(r'\d{2}:\d{2}', texto_bruto)
                if not horario_match: continue
                
                data_match = re.search(r'\d{2}\.\d{2}\.', texto_bruto)
                h_texto = horario_match.group()
                d_texto = data_match.group() if data_match else hoje_str

                # --- TRAVA UTC 2H ---
                # Aceita hoje OU amanhã até 02:00 UTC (23:00 Brasília)
                if d_texto == amanha_str:
                    if int(h_texto.split(':')[0]) >= 2: continue
                elif d_texto != hoje_str:
                    continue

                # 3. Conversão para Brasília
                h_obj = datetime.strptime(h_texto, "%H:%M")
                h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")

                # 4. Limpeza de Nomes (Evita o erro 'PREVIEW')
                linhas = [l.strip() for l in texto_bruto.split('\n') if l.strip()]
                termos_sujeira = ['PREVIEW', 'LIVE', 'AO VIVO', 'ENCERRADO', 'FIM', 'INTERVALO', 'AUDIO', 'ESTATÍSTICAS']
                
                nomes = []
                for l in linhas:
                    # Se não for horário, nem data, nem placar, nem termo de sujeira
                    if (":" not in l and "." not in l and 
                        not re.search(r'^\d+$', l) and 
                        l.upper() not in termos_sujeira and 
                        len(l) > 2):
                        nomes.append(l)

                if len(nomes) >= 2:
                    home, away = nomes[0], nomes[1]
                    lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                    contagem += 1
                
                if contagem >= 80: break
            except:
                continue

        enviar_telegram(lista_final if contagem > 0 else "⚠️ Nenhum jogo agendado para o restante do dia.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                
