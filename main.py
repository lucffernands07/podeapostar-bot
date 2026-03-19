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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_teste_individual():
    t1_name = "Bahia"
    t2_name = "Red Bull Bragantino"
    
    print(f"\n🚀 === INICIANDO TESTE DE RASPAGEM (BUSCA + INDIVIDUAL) === 🚀")
    
    driver = configurar_browser()
    wait = WebDriverWait(driver, 25)
    
    try:
        # [PROCESSO 1] BUSCA DO ID (IGUAL AO ORIGINAL)
        print(f"[LOG 1] Acessando SofaScore para buscar o confronto...")
        driver.get("https://www.sofascore.com/pt/")
        
        try:
            cookies = driver.find_elements(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Agree')]")
            if cookies: cookies[0].click()
        except: pass

        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(10)
        
        # Pega o link real para montar a URL de estatística
        resultado_xpath = "//a[contains(@href, '/football/match/')]"
        resultados = driver.find_elements(By.XPATH, resultado_xpath)
        if not resultados:
            print("❌ Falha na busca inicial.")
            return

        url_confronto = resultados[0].get_attribute("href")
        print(f"✅ ID Encontrado! URL do Jogo: {url_confronto}")
        
        driver.get(url_confronto)
        time.sleep(7)

        # --- FUNÇÃO DE RASPAGEM COM CLIQUE VIA JS (EVITA INTERCEPTAÇÃO) ---
        def raspar_dados_time(xpath_clique_time, nome_log):
            try:
                print(f"[LOG] Acessando perfil de: {nome_log}...")
                elemento_time = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_clique_time)))
                driver.execute_script("arguments[0].click();", elemento_time)
                
                print(f"[LOG] Abrindo aba 'Estatísticas' de {nome_log}...")
                btn_stats = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab:statistics']")))
                driver.execute_script("arguments[0].click();", btn_stats)
                
                # Aguarda um tempo fixo maior para garantir que o JS do Sofa carregue os números
                print(f"[LOG] Aguardando carregamento dos dados (12s)...")
                time.sleep(12) 
                
                # Rola a página para garantir que o 'Lazy Load' seja disparado
                driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(3)

                # --- ESTRATÉGIA DE RASPAGEM POR TEXTO BRUTO (ESTILO ANTIGO) ---
                texto_pagina = driver.find_element(By.TAG_NAME, "body").text
                
                # Regex que procura a frase e captura o primeiro número que vier depois (ex: 12.2 ou 12,2)
                # O \s* captura espaços e o (\d+[\.,]\d+) captura o número decimal
                busca = re.search(r"Total de finalizações por jogo\s*(\d+[\.,]\d+)", texto_pagina, re.IGNORECASE)
                
                if busca:
                    valor_str = busca.group(1).replace(',', '.')
                    valor = float(valor_str)
                    print(f"✅ [SUCESSO] {nome_log}: {valor}")
                else:
                    print(f"❌ [AVISO] Frase 'Total de finalizações por jogo' não encontrada no texto de {nome_log}.")
                    # Log preventivo: imprimir um pedaço do texto para ver o que o robô está lendo
                    print(f"[DEBUG] Começo do texto lido: {texto_pagina[:200]}...")
                    valor = 0

                driver.get(url_confronto)
                return valor

            except Exception as e:
                print(f"❌ [ERRO] Falha geral no processo de {nome_log}")
                driver.get(url_confronto)
                return 0
                
        # Executa para os dois
        # XPath do bdi que você forneceu para o Bahia e Bragantino
        media_casa = raspar_dados_time(f"//bdi[contains(text(), '{t1_name}')]", t1_name)
        media_fora = raspar_dados_time(f"//bdi[contains(text(), '{t2_name}')]", t2_name)

        # CÁLCULO
        print(f"\n📊 === RESULTADO FINAL === 📊")
        if media_casa > 0 and media_fora > 0:
            media_final = (media_casa + media_fora) / 2
            print(f"🎯 Média Bahia: {media_casa} | Média Bragantino: {media_fora}")
            print(f"📈 Resultado: {media_final:.2f}")
            
            if media_final > 10.5:
                print("✅ APROVADO (> 10.5)")
            else:
                print("⚠️ REJEITADO (<= 10.5)")
        else:
            print("❌ Falha ao obter uma ou ambas as médias.")

    except Exception as e:
        print(f"❌ Erro Mestre: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    executar_teste_individual()
                      
