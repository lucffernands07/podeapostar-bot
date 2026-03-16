import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
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

def executar_fluxo_completo(time_casa, time_fora):
    driver = configurar_browser()
    wait = WebDriverWait(driver, 20)
    
    print(f"\n🚀 --- INICIANDO FLUXO: {time_casa} x {time_fora} ---")
    
    try:
        # 1. ACESSAR LINK INICIAL
        print("🏠 Passo 1: Acessando Home do SofaScore...")
        driver.get("https://www.sofascore.com/pt/")
        
        # 2. BUSCAR O JOGO
        print(f"🔍 Passo 2: Buscando por '{time_casa} {time_fora}'...")
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        search_input.send_keys(f"{time_casa} {time_fora}")
        time.sleep(6) # Tempo para os resultados aparecerem
        
        # 3. CAPTURAR O ID/LINK (LOG DA ID)
        print("🔗 Passo 3: Localizando link do jogo nos resultados...")
        # Procura um link que contenha os nomes dos times e o padrão de partida
        resultado_link = wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/football/match/') and (contains(., '{time_casa}') or contains(., '{time_fora}'))]")))
        url_jogo = resultado_link.get_attribute("href")
        
        print(f"📊 LOG DA ID/URL ENCONTRADA: {url_jogo}")

        # 4. ACESSAR ABA PARTIDAS H2H
        url_h2h = url_jogo.split('#')[0] + "#tab:matches"
        print(f"📡 Passo 4: Indo para aba Partidas H2H: {url_h2h}")
        driver.get(url_h2h)
        
        # Espera o carregamento e faz o scroll necessário
        time.sleep(12)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        print("📜 Rolando a página para carregar cards de estatísticas...")
        time.sleep(5)

        # 5. RASPAR FRAÇÃO DE ESCANTEIO
        print("✂️ Passo 5: Raspando frações do texto bruto...")
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        fracoes_encontradas = []
        # Mesma lógica do código antigo validado
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        for m in matches:
            trecho = texto_bruto[m.end() : m.end() + 50]
            busca_frequencia = re.search(r"(\d+)/(\d+)", trecho)
            if busca_frequencia:
                num, den = busca_frequencia.group(1), busca_frequencia.group(2)
                item = f"{num}/{den}"
                # Evita duplicatas se o dado aparecer mais de uma vez
                if item not in fracoes_encontradas:
                    fracoes_encontradas.append(item)
                    print(f"✅ Fração capturada: {item}")

        # RESULTADO FINAL E ENVIO
        if len(fracoes_encontradas) >= 2:
            f1, f2 = fracoes_encontradas[0], fracoes_encontradas[1]
            p1 = (int(f1.split('/')[0]) / int(f1.split('/')[1])) * 100
            p2 = (int(f2.split('/')[0]) / int(f2.split('/')[1])) * 100
            media = (p1 + p2) / 2
            
            relatorio = (
                f"🎫 *RELATÓRIO H2H*\n"
                f"🏟️ {time_casa} x {time_fora}\n"
                f"🚩 Menos 10.5 Escanteios\n\n"
                f"🏠 Casa: {f1} ({p1:.1f}%)\n"
                f"🚌 Fora: {f2} ({p2:.1f}%)\n"
                f"📊 Média: {media:.1f}%"
            )
            print("\n📈 Resultado calculado com sucesso!")
            
            # Envio ao Telegram (opcional para o seu teste de log)
            if TOKEN and CHAT_ID:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              json={"chat_id": CHAT_ID, "text": relatorio, "parse_mode": "Markdown"})
        else:
            print(f"⚠️ Aviso: Apenas {len(fracoes_encontradas)} frações encontradas. O site pode não ter o H2H completo ainda.")

    except Exception as e:
        print(f"🚨 ERRO DURANTE O FLUXO: {e}")
    finally:
        driver.quit()
        print("\n🏁 Fim do teste.")

if __name__ == "__main__":
    executar_fluxo_completo("Cremonese", "Fiorentina")
            
