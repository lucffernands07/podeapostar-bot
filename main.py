import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def raspar_h2h_inteligente(url_jogo, casa_nome, fora_nome):
    driver = configurar_browser()
    url_final = url_jogo + "#tab:matches"
    
    print(f"\n🚀 --- INICIANDO EXTRAÇÃO: {casa_nome} x {fora_nome} ---")
    
    try:
        driver.get(url_final)
        time.sleep(10)
        
        # Scroll para carregar os componentes de estatísticas
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Vamos encontrar todos os containers de estatísticas (H2H)
        # O SofaScore agrupa os dados do time da casa e do visitante em seções separadas
        containers = soup.find_all('div', class_=re.compile(r'sc-.*')) # Busca divs de componentes

        print(f"📊 LOG: Analisando blocos de estatísticas para {casa_nome} e {fora_nome}...")

        resultados = {}
        times_alvo = [casa_nome, fora_nome]
        
        # Pegamos o texto bruto para extrair as frações de forma linear
        texto_bruto = soup.get_text(separator=' ')
        
        # Regex para achar "Menos de 10.5" ou "10.5 escanteios" seguido de fração
        pattern = r"10\.5\s+escanteios.*?(\d+)/(\d+)"
        matches = re.findall(pattern, texto_bruto, re.IGNORECASE)

        if len(matches) >= 2:
            # Seguindo sua lógica: a primeira ocorrência relevante para o contexto da casa
            # e a primeira ocorrência relevante para o contexto de fora.
            # No layout H2H, a lista costuma ser: [CASA, CASA, CASA..., FORA, FORA, FORA...]
            # Mas como os escanteios 10.5 são específicos, pegamos as ocorrências:
            
            # Nota: Em muitos jogos, a 7ª e 8ª ocorrência no texto total 
            # correspondem exatamente ao primeiro '10.5' da Casa e o primeiro '10.5' do Fora.
            
            v_casa_num, v_casa_den = map(int, matches[6]) # 7ª ocorrência (índice 6)
            v_fora_num, v_fora_den = map(int, matches[7]) # 8ª ocorrência (índice 7)

            perc_casa = (v_casa_num / v_casa_den) * 100
            perc_fora = (v_fora_num / v_fora_den) * 100

            print(f"\n✅ LOG: Sucesso na extração!")
            print(f"🏠 {casa_nome} (10.5 Esc): {v_casa_num}/{v_casa_den} -> {perc_casa:.1f}%")
            print(f"🚌 {fora_nome} (10.5 Esc): {v_fora_num}/{v_fora_den} -> {perc_fora:.1f}%")
            print(f"📈 MÉDIA: {(perc_casa + perc_fora)/2:.1f}%")
        else:
            print(f"⚠️ LOG: Não foi possível encontrar as duas frações de 10.5. Total encontrado: {len(matches)}")

    except Exception as e:
        print(f"🚨 ERRO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Link obtido no teste de ID
    url = "https://www.sofascore.com/pt/football/match/lazio-milan/RdbsZdb#id:13981707"
    raspar_h2h_inteligente(url, "Lazio", "Milan")
