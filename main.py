import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def testar_spans_panathinaikos():
    print("🚀 Iniciando teste de raspagem no Panathinaikos...")
    
    options = Options()
    options.add_argument("--headless")  # Roda sem abrir janela
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # URL de busca direta para o H2H do jogo no SofaScore
    jogo = "Panathinaikos vs Real Betis"
    query = urllib.parse.quote(f"sofascore h2h {jogo}")
    url_busca = f"https://www.google.com/search?q={query}"

    try:
        driver.get(url_busca)
        
        # 1. Clica no primeiro resultado do Google
        print("🔍 Buscando link no Google...")
        first_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
        first_link.click()
        
        print(f"✅ Entrou no site: {driver.current_url}")
        print("⏳ Aguardando 15 segundos para carregar os cards de estatísticas...")
        
        # 2. Espera forçada para o SofaScore carregar os scripts internos
        time.sleep(15)
        
        # 3. Busca todos os spans que podem conter a informação
        # Usamos a classe que você mapeou e seletores de texto
        spans_estatisticas = driver.find_elements(By.CLASS_NAME, "textStyle_table")
        
        print("\n--- RESULTADOS ENCONTRADOS ---")
        encontrou_algo = False
        
        for span in spans_estatisticas:
            texto = span.text.strip()
            if texto:
                # Se encontrar qualquer menção a escanteios, imprime com destaque
                if "escanteios" in texto.lower():
                    print(f"🔥 ACHOU: {texto}")
                    encontrou_algo = True
                else:
                    # Imprime outros spans para sabermos o que o robô está lendo
                    print(f"ℹ️ Outro card: {texto}")

        if not encontrou_algo:
            print("\n❌ Nenhum span de escanteio foi detectado com a classe 'textStyle_table'.")
            print("💡 Tentando busca geral por texto...")
            geral = driver.find_elements(By.XPATH, "//*[contains(text(), '10.5')]")
            for g in geral:
                print(f"🔎 Possível alvo: {g.text}")

    except Exception as e:
        print(f"⚠️ Erro durante o teste: {e}")
    
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_spans_panathinaikos()
