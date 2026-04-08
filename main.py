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
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Simula exatamente um desktop em tela cheia para evitar a versão mobile simplificada
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = configurar_driver()
    lista_final = "🏆 *Lista de Jogos (Recuperação Sniper)*\n\n"
    
    agora_utc = datetime.now()
    hoje_str = agora_utc.strftime("%d.%m.")
    amanha_str = (agora_utc + timedelta(days=1)).strftime("%d.%m.")

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10) # Tempo generoso para o JavaScript carregar tudo

            # Tenta pegar qualquer div que tenha a classe de partida (event__match)
            # ou os IDs que começam com g_1_
            jogos = driver.find_elements(By.XPATH, "//*[contains(@id, 'g_1_')] | //*[contains(@class, 'event__match')]")
            
            if not jogos:
                continue

            secao_adicionada = False
            for jogo in jogos:
                try:
                    texto = jogo.text
                    if not texto or ":" not in texto: continue
                    
                    # Filtro de status
                    if any(x in texto.upper() for x in ['LIVE', 'AO VIVO', 'ENCERRADO', 'FIM', 'INTERROMPIDO']):
                        continue

                    # Extração de Horário e Data
                    h_match = re.search(r'(\d{2}:\d{2})', texto)
                    if not h_match: continue
                    h_utc = h_match.group(1)

                    d_match = re.search(r'(\d{2}\.\d{2}\.)', texto)
                    d_site = d_match.group(1) if d_match else hoje_str

                    # Trava das 2h UTC
                    if d_site == amanha_str:
                        if int(h_utc.split(':')[0]) >= 2: continue
                    elif d_site != hoje_str and d_site != amanha_str:
                        continue

                    # Busca os nomes dos times dentro do elemento atual por classe
                    # Isso é mais seguro que split de texto
                    try:
                        home = jogo.find_element(By.CSS_SELECTOR, ".event__participant--home").text
                        away = jogo.find_element(By.CSS_SELECTOR, ".event__participant--away").text
                    except:
                        # Fallback se as classes falharem (limpeza de linhas)
                        linhas = [l.strip() for l in texto.split('\n') if len(l.strip()) > 2]
                        # Remove horário e termos inúteis
                        limpos = [l for l in linhas if ":" not in l and "." not in l and l.upper() not in ['PREVIEW', 'AUDIO', 'ESTATÍSTICAS']]
                        if len(limpos) >= 2:
                            home, away = limpos[0], limpos[1]
                        else: continue

                    if home and away:
                        h_br = (datetime.strptime(h_utc, "%H:%M") - timedelta(hours=3)).strftime("%H:%M")
                        if not secao_adicionada:
                            lista_final += f"--- {nome_comp} ---\n"
                            secao_adicionada = True
                        lista_final += f"🕒 `{h_br}` | *{home} x {away}*\n"
                except: continue
            
            if secao_adicionada: lista_final += "\n"
        
        if "🕒" not in lista_final:
            # Se falhar tudo, tenta ao menos pegar o título da página para saber onde estamos
            enviar_telegram(f"⚠️ Erro: Página carregou como '{driver.title}', mas nenhum jogo foi filtrado.")
        else:
            enviar_telegram(lista_final)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
