import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # Simular Desktop para carregar mais cards
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_logica_antiga_v2(url_base):
    driver = configurar_browser()
    
    # Limpa a URL para evitar o erro de duplo '#'
    url_limpa = url_base.split('#')[0]
    print(f"\n🚀 --- EXECUTANDO LOGICA REVISADA ---")
    print(f"🔗 Alvo: {url_limpa}")
    
    try:
        driver.get(url_limpa)
        wait = WebDriverWait(driver, 20)

        # 1. CLICAR NA ABA PARTIDAS (Garante que estamos no lugar certo)
        print("🖱️ Clicando na aba Partidas...")
        try:
            # Busca o link que contém 'tab:matches' ou o texto 'Partidas'
            aba_partidas = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'tab:matches')] | //div[text()='Partidas']")))
            driver.execute_script("arguments[0].click();", aba_partidas)
        except Exception as e:
            print(f"⚠️ Aviso: Nao foi possivel clicar na aba (pode ja estar nela). Erro: {e}")

        # 2. SCROLL PARA BAIXO (Essencial para os cards aparecerem)
        print("📜 Rolando a pagina para carregar os cards...")
        time.sleep(3)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(5) # Espera o JS carregar os dados

        # 3. PEGAR TEXTO BRUTO
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # 4. SCANNER DE ESCANTEIOS (IGUAL AO SEU ANTIGO)
        frequencias = []
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        print("\n🔍 Analisando texto capturado...")
        
        for i, m in enumerate(matches, 1):
            trecho_apos = texto_bruto[m.end() : m.end() + 50]
            frequencia = re.search(r"(\d+)/(\d+)", trecho_apos)
            
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)
                print(f"✅ [{i}] Encontrado: {num}/{den} ({perc:.1f}%)")

        if len(frequencias) >= 2:
            f1, f2 = frequencias[0], frequencias[1]
            print(f"\n📊 RESULTADO: Casa {f1:.1f}% | Fora {f2:.1f}%")
        else:
            print(f"❌ ERRO: Apenas {len(frequencias)} fracoes encontradas. Texto capturado foi muito curto?")
            # Print de debug para ver o que o robô está lendo
            print(f"📝 Inicio do texto lido: {texto_bruto[:200]}...")

    except Exception as e:
        print(f"🚨 ERRO CRITICO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.sofascore.com/pt/football/match/lazio-milan/RdbsZdb#id:13981707"
    testar_logica_antiga_v2(url)
    
