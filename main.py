import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES (Pegando das variáveis do GitHub) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def buscar_id_direto(driver, t1, t2):
    """ Busca via URL de pesquisa para evitar erros de clique no menu """
    print(f"🔍 Buscando link para: {t1} x {t2}...")
    url_busca = f"https://www.sofascore.com/pt/busca?q={t1}+{t2}"
    driver.get(url_busca)
    time.sleep(8) 
    
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        href = link.get_attribute("href")
        if href and "/football/match/" in href:
            if t1.lower() in href.lower() or t2.lower() in href.lower():
                # Retorna a URL base sem o resto
                return href.split('#')[0]
    return None

def extrair_dados_h2h(driver, url_jogo):
    """ A lógica que funcionou: Aba Partidas + Scroll + Texto Bruto """
    url_final = url_jogo + "#tab:matches"
    print(f"📡 Acessando H2H: {url_final}")
    driver.get(url_final)
    
    # Espera generosa para garantir que os cards carreguem
    time.sleep(12)
    
    # Rola a página para baixo (essencial para renderizar os cards)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
    time.sleep(5)
    
    texto_bruto = driver.find_element(By.TAG_NAME, "body").text
    
    frequencias_percs = []
    fracoes_unicas = []
    
    # Scanner de frações
    matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
    for m in matches:
        trecho = texto_bruto[m.end() : m.end() + 50]
        busca = re.search(r"(\d+)/(\d+)", trecho)
        if busca:
            num, den = busca.group(1), busca.group(2)
            fracao = f"{num}/{den}"
            # Evita duplicatas do mesmo dado que o SofaScore às vezes repete no texto
            if fracao not in fracoes_unicas:
                fracoes_unicas.append(fracao)
                p = (int(num) / int(den)) * 100
                frequencias_percs.append(p)
                print(f"✅ Capturado: {fracao} ({p:.1f}%)")
    
    return fracoes_unicas, frequencias_percs

def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        print("❌ Erro ao enviar Telegram")

def executar():
    driver = configurar_browser()
    # No futuro, aqui você pode colocar um loop vindo da API-Football
    time_casa, time_fora = "Lazio", "Milan"
    
    url = buscar_id_direto(driver, time_casa, time_fora)
    if url:
        fracoes, percs = extrair_dados_h2h(driver, url)
        
        # O código antigo pegava as 2 primeiras. Aqui garantimos que temos 2 diferentes.
        if len(percs) >= 2:
            p_casa, p_fora = percs[0], percs[1]
            media = (p_casa + p_fora) / 2
            
            msg = f"🏟️ *{time_casa} x {time_fora}*\n🚩 Menos 10.5 Escanteios\n\n"
            msg += f"🏠 Casa: {fracoes[0]} ({p_casa:.1f}%)\n"
            msg += f"🚌 Fora: {fracoes[1]} ({p_fora:.1f}%)\n"
            msg += f"📊 Média: {media:.1f}%\n"
            
            if p_casa >= 90 and p_fora >= 90:
                msg += "\n🔥 *PALPITE: PRIORITÁRIO*"
            elif media >= 85:
                msg += "\n✅ *PALPITE: APROVADO*"
            
            enviar_telegram(msg)
            print(f"🚀 Relatório enviado!")
        else:
            print(f"⚠️ Apenas {len(percs)} frações encontradas. Requisito mínimo: 2.")
    else:
        print(f"❌ Jogo {time_casa} x {time_fora} não localizado.")
    
    driver.quit()

if __name__ == "__main__":
    executar()
            
