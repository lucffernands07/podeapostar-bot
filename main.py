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
    lista_final = "🏆 *Próximos Jogos de Hoje (Filtro 23h Brasília)*\n\n"
    
    # Datas de referência
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
                    
                    # 1. Ignora jogos que já começaram ou terminaram
                    status_ignore = ['LIVE', 'AO VIVO', 'INTERVALO', 'FIM', 'ENCERRADO', 'ADIADO']
                    if any(x in texto.upper() for x in status_ignore):
                        continue
                    
                    # 2. Pega Horário e Data do texto
                    horario_match = re.search(r'\d{2}:\d{2}', texto)
                    data_match = re.search(r'\d{2}\.\d{2}\.', texto)
                    if not horario_match: continue
                    
                    h_texto = horario_match.group()
                    d_texto = data_match.group() if data_match else hoje_str

                    # --- LOGICA DA TRAVA UTC ---
                    # Se for do dia seguinte (UTC), só aceita se for até as 02:00 (que é 23h Brasília)
                    if d_texto == amanha_str:
                        hora_int = int(h_texto.split(':')[0])
                        if hora_int > 2: # Se for 03:00 UTC pra frente, já é amanhã de verdade no BR
                            continue
                    elif d_texto != hoje_str:
                        continue # Pula datas muito distantes

                    # 3. Conversão para Brasília
                    h_obj = datetime.strptime(h_texto, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    # 4. Captura de Nomes
                    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                    nomes = [l for l in linhas if ":" not in l and "." not in l and not re.search(r'^\d+$', l) and len(l) > 2]

                    if len(nomes) >= 2:
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        lista_final += f"🕒 `{h_br}` | *{nomes[0]} x {nomes[1]}*\n"
                except: continue
            
            if secao_adicionada: lista_final += "\n"
        
        enviar_telegram(lista_final if "🕒" in lista_final else "⚠️ Nenhum jogo agendado encontrado.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                    
