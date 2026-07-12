import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    # 🔗 A URL do H2H que você enviou
    url_h2h = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/goias-hfAZyE0t/h2h/total/"
    
    print("\n🔍 INICIANDO TESTE #43 (CAÇA AO 'mid' NAS LINHAS DO H2H)\n" + "="*60)
    print(f"🔗 Analisando histórico em: {url_h2h}")
    
    try:
        driver.get(url_h2h)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(3.0)
        
        # Captura as linhas brutas do H2H (as divs que englobam o HTML que você mandou)
        linhas_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
        print(f"📊 Linhas de confrontos encontradas no H2H: {len(linhas_h2h)}\n")
        
        print("📝 INSPEÇÃO DOS ATRIBUTOS DAS 5 PRIMEIRAS LINHAS:")
        print("-" * 60)
        
        for idx, linha in enumerate(linhas_h2h[:5]):
            # Vamos extrair tudo o que essa linha pai possui no HTML para achar o ID oculto
            html_id = linha.get_attribute("id")
            html_class = linha.get_attribute("class")
            html_data_id = list(driver.execute_script("""
                var items = {};
                for (index = 0; index < arguments[0].attributes.length; ++index) {
                    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value;
                };
                return items;
            """, linha).items())
            
            # Tenta buscar também se existe algum link interno oculto ali dentro
            link_interno = "Não encontrado"
            try:
                tag_a = linha.find_element(By.XPATH, "./preceding-sibling::a | .//a | ..")
                link_interno = tag_a.get_attribute("href")
            except: pass
            
            print(f"📈 [LINHA JOGO #{idx+1}]")
            print(f"   🆔 Atributo 'id' direto: '{html_id}'")
            print(f"   👥 Todos os Atributos: {html_data_id}")
            print(f"   🔗 Link associado (href): {link_interno}")
            print("-" * 40)
            
    except Exception as e:
        print(f"\n❌ Erro ao caçar atributos no H2H: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #43")

if __name__ == "__main__":
    rodar_teste_isolado()
    
