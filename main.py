import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def testar_link_direto():
    # O link que você me passou
    url = "https://www.sofascore.com/pt/football/match/panathinaikos-fc-real-betis/qgbsYob"
    
    print(f"🚀 Acessando link direto: {url}")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # User-Agent para o SofaScore não bloquear o acesso
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        
        # O SofaScore carrega as estatísticas de confronto (H2H) via JavaScript
        # Precisamos de um tempo para os "Cards" aparecerem na tela
        print("⏳ Aguardando 15 segundos para os cards carregarem...")
        time.sleep(15)
        
        # Buscamos os spans com a classe que você mapeou ou pelo texto
        print("🔎 Procurando padrões de escanteio (Menos/Mais 10.5)...")
        
        # Procura especificamente o texto que está no seu print
        elementos = driver.find_elements(By.XPATH, "//*[contains(text(), '10.5')]")
        
        if not elementos:
            print("❌ Não encontrou texto '10.5'. Tentando capturar todos os spans da tabela...")
            elementos = driver.find_elements(By.CLASS_NAME, "textStyle_table")

        for el in elementos:
            texto = el.text.strip()
            if texto:
                # Filtra apenas o que interessa (escanteios e a frequência como 10/10)
                if "escanteio" in texto.lower() or "/" in texto:
                    print(f"✅ VALOR ENCONTRADO: {texto}")

    except Exception as e:
        print(f"⚠️ Erro ao acessar o link: {e}")
    
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_link_direto()
