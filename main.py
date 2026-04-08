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

# Foco total no que você opera
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
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Análise das Competições (Filtro 23h BR)*\n\n"
    
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(4)
            
            jogos = driver.find_elements(By.CSS_SELECTOR, "[id^='g_1_']")
            secao_adicionada = False
            
            for jogo in jogos:
                try:
                    texto = jogo.text
                    
                    # 1. Ignora jogos ao vivo ou encerrados
                    if any(x in texto.upper() for x in ['LIVE', 'AO VIVO', 'INTERVALO', 'FIM', 'ENCERRADO']):
                        continue
                    
                    # 2. Captura Horário e Data
                    horario_match = re.search(r'\d{2}:\d{2}', texto)
                    if not horario_match: continue
                    
                    data_match = re.search(r'\d{2}\.\d{2}\.', texto)
                    h_texto = horario_match.group()
                    d_texto = data_match.group() if data_match else hoje_str

                    # 3. Trava 2h UTC (Até 23:00 de Brasília)
                    if d_texto == amanha_str:
                        if int(h_texto.split(':')[0]) >= 2: continue
                    elif d_texto != hoje_str:
                        continue

                    # 4. Limpeza de nomes e remoção do 'PREVIEW'
                    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                    # Termos que queremos ignorar para sobrar apenas os times
                    sujeira = ['PREVIEW', 'AUDIO', 'ESTATÍSTICAS', 'VÍDEO']
                    
                    nomes = []
                    for l in linhas:
                        if (":" not in l and "." not in l and 
                            not re.search(r'^\d+$', l) and 
                            l.upper() not in sujeira and 
                            len(l) > 2):
                            nomes.append(l)

                    if len(nomes) >= 2:
                        h_br = (datetime.strptime(h_texto, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                        
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        
                        lista_final += f"🕒 `{h_br}` | *{nomes[0]} x {nomes[1]}*\n"
                except: continue
            
            if secao_adicionada: lista_final += "\n"
        
        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo agendado nas ligas de elite.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                                
