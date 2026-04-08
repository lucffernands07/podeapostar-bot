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

COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/"
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
    options.add_argument("--window-size=1920,5000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def processar_liga(driver, nome_liga, url):
    driver.get(url)
    time.sleep(7)
    jogos_da_liga = []
    
    # Data de hoje para comparação (08/04)
    hoje_ref = datetime.now().day

    try:
        abas = driver.find_elements(By.CSS_SELECTOR, ".tabs__tab")
        for aba in abas:
            if "PRÓXIMOS" in aba.text.upper():
                driver.execute_script("arguments[0].click();", aba)
                time.sleep(5)
                break
    except: pass

    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match, [id^='g_1_']")
    
    for el in elementos:
        try:
            # Captura o texto e limpa espaços extras
            texto = " ".join(el.text.split())
            
            # REGEX MELHORADO: Pega horário, Time 1, Hífen, Time 2. 
            # Para o Time 2, ele para assim que encontrar palavras como 'ESTATÍSTICAS' ou espaços duplos
            match = re.search(r'(\d{2}:\d{2})\s+([^-(]+)\s+-\s+([^-(]+)', texto)
            
            if match:
                h_utc = match.group(1)
                t1 = match.group(2).strip()
                t2 = match.group(3).strip()

                # Limpeza fina para tirar resíduos de nomes de times com parênteses ou lixo do site
                t2 = re.split(r'ESTATÍSTICAS|PREVIEW|AUDIO|venc|perdeu', t2)[0].strip()

                # --- CORREÇÃO DO FUSO E TRAVA DE DATA ---
                h_obj = datetime.strptime(h_utc, "%H:%M")
                # Se o horário UTC for baixo (00h, 01h), é sinal que no servidor já virou o dia
                # Mas no Brasil ainda é o jogo da noite de HOJE.
                h_br_obj = h_obj - timedelta(hours=3)
                h_br = h_br_obj.strftime("%H:%M")

                # FILTRO PARA NÃO PEGAR AMANHÃ:
                # 1. Se a hora de Brasília for entre 11:00 e 23:59, é jogo de HOJE.
                # 2. Se a hora UTC for >= 03:00 e o site indicar outra data (não visível aqui mas implícito na aba),
                #    nós ignoramos para não pegar a rodada de amanhã da Champions.
                if 11 <= h_br_obj.hour <= 23:
                    # Trava específica para Champions: Se for 16h (BR), mas o UTC original for de "amanhã"
                    # Como o texto bruto às vezes traz a data antes, verificamos:
                    if "amanhã" in texto.lower() or (h_obj.hour >= 3 and h_obj.hour < 10 and "Champions" in nome_liga):
                        continue
                        
                    jogos_da_liga.append(f"🕒 `{h_br}` | *{t1} x {t2}*")
        except: continue
    
    # Remove duplicados mantendo a ordem
    return list(dict.fromkeys(jogos_da_liga))

def main():
    driver = configurar_driver()
    data_formatada = datetime.now().strftime('%d/%m')
    mensagem_final = f"🏆 *JOGOS DE HOJE - {data_formatada}*\n\n"
    encontrou_algo = False

    try:
        for nome, url in COMPETICOES.items():
            print(f"Analisando {nome}...")
            jogos = processar_liga(driver, nome, url)
            
            if jogos:
                encontrou_algo = True
                mensagem_final += f"--- {nome} ---\n"
                mensagem_final += "\n".join(jogos) + "\n\n"

        if encontrou_algo:
            enviar_telegram(mensagem_final)
            print("Mensagem enviada!")
        else:
            enviar_telegram(f"⚠️ Nenhum jogo encontrado para {data_formatada}.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
