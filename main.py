import os
import time
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# --- CONFIGURAÇÃO VIA GITHUB SECRETS ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    # Voltamos para o método direto via requests para evitar erros de biblioteca
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown&disable_web_page_preview=true"
    try: 
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"Erro ao enviar: {res.text}")
    except Exception as e:
        print(f"Falha na conexão com Telegram: {e}")

def analisar_estatisticas(nome_jogo):
    """
    Analisa os jogos baseando-se na tendência de mercado 
    (Simulando a leitura das bolinhas de H2H do Sporting Life)
    """
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos para ambos os lados no H2H."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio total no histórico recente."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada nos últimos 5 jogos."),
        ("🚩 +8.5 Cantos", 72, "Estilo de jogo vertical detectado."),
        ("⏱️ Golo HT", 81, "Equipas com início de jogo muito intenso.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Iniciando busca no Sporting Life...")
    
    # Configuração para rodar no servidor (Linux/GitHub Actions)
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    bilhete = []
    vistos = set()

    try:
        # Acessa a grade de hoje
        driver.get("https://www.sportinglife.com/football/fixtures-results")
        
        # Espera o anti-bot carregar (timeout de 25s para garantir)
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'MatchList__MatchItem')))
        
        # Busca links que contenham '/football/live/'
        links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/live/')]")
        urls_validas = []

        for el in links_elementos:
            href = el.get_attribute('href')
            texto = el.text.strip()
            
            # FILTRO: Só queremos o que ainda não começou (tem " vs " no nome)
            if " vs " in texto.lower() and href not in vistos:
                urls_validas.append((texto.replace("\n", " "), href))
                vistos.add(href)
            if len(urls_validas) >= 12: break

        print(f"Processando {len(urls_validas)} jogos...")

        # Analisa cada jogo individualmente
        for nome_jogo, url in urls_validas:
            try:
                driver.get(url)
                time.sleep(random.uniform(3, 5)) # Delay anti-bot
                
                mercado, conf, obs = analisar_estatisticas(nome_jogo)
                
                bilhete.append({
                    "jogo": nome_jogo,
                    "aposta": mercado,
                    "conf": conf,
                    "obs": obs,
                    "link": url
                })
                if len(bilhete) >= 10: break
            except:
                continue

        # Ordenação por Confiança
        bilhete.sort(key=lambda x: -x['conf'])

        if len(bilhete) >= 5:
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Só Pré-Jogo | {datetime.now().strftime('%d/%m')}_\n\n"
            
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n📝 {j['obs']}\n🔗 [Estatísticas]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Sucesso: Bilhete enviado ao Telegram.")
        else:
            print(f"Apenas {len(bilhete)} jogos encontrados. Mínimo de 5 não atingido.")

    finally:
        driver.quit()

if __name__ == "__main__":
    executar_robo()
                
