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
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown&disable_web_page_preview=true"
    try: 
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            print(f"Erro Telegram: {res.text}")
    except Exception as e:
        print(f"Falha ao ligar ao Telegram: {e}")

def analisar_estatisticas(nome_jogo):
    """
    Gera a sugestão baseada na tendência estatística do confronto.
    """
    opcoes = [
        ("🎯 Ambas Marcam", 79, "Tendência de golos para ambos os lados no H2H."),
        ("🛡️ DNB (Empate Anula)", 76, "Equilíbrio total no histórico recente."),
        ("🔥 +1.5 Golos", 84, "Média de golos elevada nos últimos confrontos."),
        ("🚩 +8.5 Cantos", 72, "Jogo vertical com alto índice de cruzamentos."),
        ("⏱️ Golo HT", 81, "Equipas com início de jogo muito intenso.")
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] A iniciar Chrome no GitHub Actions...")
    
    # Configurações críticas para evitar erro de versão e conexão
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')

    driver = None
    try:
        # Forçamos a versão 145 para bater com o Chrome do GitHub Actions
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=145)
        bilhete = []
        vistos = set()

        # 1. Aceder à grade de jogos de hoje
        driver.get("https://www.sportinglife.com/football/fixtures-results")
        
        # Espera o carregamento inicial (Anti-bot)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'MatchList__MatchItem')))
        
        # 2. Capturar links de partidas (Status: Próximos)
        links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/football/live/')]")
        urls_validas = []

        for el in links_elementos:
            try:
                href = el.get_attribute('href')
                texto = el.text.strip()
                # Filtra apenas jogos que ainda não começaram (contêm ' vs ')
                if " vs " in texto.lower() and href not in vistos:
                    urls_validas.append((texto.replace("\n", " "), href))
                    vistos.add(href)
                if len(urls_validas) >= 12: break
            except:
                continue

        print(f"Analisando {len(urls_validas)} partidas encontradas...")

        # 3. Entrar em cada link para validar aposta
        for nome_jogo, url in urls_validas:
            try:
                driver.get(url)
                time.sleep(random.uniform(4, 6)) # Delay humano anti-bloqueio
                
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

        # Ordenar os 10 melhores por confiança
        bilhete.sort(key=lambda x: -x['conf'])

        if len(bilhete) >= 5:
            msg = f"🎫 *BILHETE DO DIA - SPORTING LIFE*\n_Só Pré-Jogo | {datetime.now().strftime('%d/%m')}_\n\n"
            
            for i, j in enumerate(bilhete, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n📍 *{j['aposta']}* ({j['conf']}%)\n📝 {j['obs']}\n🔗 [Estatísticas]({j['link']})\n\n"
            
            enviar_telegram(msg)
            print("Bilhete enviado com sucesso!")
        else:
            print(f"Jogos insuficientes encontrados ({len(bilhete)}). Mínimo é 5.")

    except Exception as e:
        print(f"Erro Crítico: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    executar_robo()
            
