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
    """Trata cada liga de forma isolada para evitar que o erro de uma afete a outra"""
    driver.get(url)
    time.sleep(7)
    jogos_da_liga = []

    # 1. Força a aba PRÓXIMOS
    try:
        abas = driver.find_elements(By.CSS_SELECTOR, ".tabs__tab")
        for aba in abas:
            if "PRÓXIMOS" in aba.text.upper():
                driver.execute_script("arguments[0].click();", aba)
                time.sleep(5)
                break
    except: pass

    # 2. Captura todos os blocos de jogo (Independente da estrutura de mata-mata ou grupo)
    # Buscamos tanto por IDs quanto por classes de evento
    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match, [id^='g_1_']")
    
    for el in elementos:
        try:
            texto = el.text.replace("\n", " ").strip()
            # Regex flexível: Horário + Time Home + (opcional placar) + Time Away
            # Ex: 16:00 Barcelona - Atl. Madrid
            match = re.search(r'(\d{2}:\d{2})\s+(.+?)\s*-\s*(.+)', texto)
            
            if match:
                h_utc = match.group(1)
                t1 = match.group(2).strip()
                t2 = match.group(3).strip()

                # Remove lixos comuns do texto capturado
                t2 = re.split(r'ESTATÍSTICAS|PREVIEW|AUDIO', t2)[0].strip()

                # --- CORREÇÃO DO FUSO E DATA ---
                h_obj = datetime.strptime(h_utc, "%H:%M")
                h_br_obj = h_obj - timedelta(hours=3)
                h_br = h_br_obj.strftime("%H:%M")

                # Se o horário convertido para Brasília for tarde/noite (>=11h), é hoje.
                # Isso permite que 00:30 UTC vire 21:30 Hoje sem ser bloqueado pela data.
                if h_br_obj.hour >= 11:
                    jogos_da_liga.append(f"🕒 `{h_br}` | *{t1} x {t2}*")
        except: continue
    
    return list(dict.fromkeys(jogos_da_liga)) # Remove duplicados

def main():
    driver = configurar_driver()
    mensagem_final = f"🏆 *JOGOS DE HOJE - {datetime.now().strftime('%d/%m')}*\n\n"
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
        else:
            enviar_telegram("⚠️ Nenhum jogo de hoje encontrado nas 3 ligas.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
