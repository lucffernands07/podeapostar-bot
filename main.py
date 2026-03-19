import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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

# --- FUNÇÃO DE RASPAGEM (FORA DA FUNÇÃO PRINCIPAL PARA ORGANIZAÇÃO) ---
def raspar_dados_time(driver, wait, xpath_clique_time, nome_log, url_confronto):
    try:
        print(f"\n[LOG] Passo 1: Entrando no perfil de {nome_log}...")
        btn_time = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_clique_time)))
        driver.execute_script("arguments[0].click();", btn_time)
        
        print(f"[LOG] Passo 2: Indo para a aba Estatísticas...")
        btn_stats = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab:statistics']")))
        driver.execute_script("arguments[0].click();", btn_stats)
        
        print(f"[LOG] Passo 3: Esperando renderização (15s)...")
        time.sleep(15) # SofaScore é lento para injetar os números no HTML
        driver.execute_script("window.scrollBy(0, 500);")

        # --- O SEU SPAN (BUSCA DIRETA PELO ELEMENTO) ---
        print(f"[LOG] Passo 4: Extraindo valor pelo SPAN específico...")
        try:
            # XPath baseado no HTML que você enviou: busca o texto e pega o próximo span (o valor)
            # Estrutura: <div> <span>Texto</span> <span>Valor</span> </div>
            xpath_valor = "//span[text()='Total de finalizações por jogo']/parent::div/span[2]"
            
            elemento_valor = wait.until(EC.presence_of_element_located((By.XPATH, xpath_valor)))
            valor_texto = elemento_valor.text.strip()
            
            # Limpeza rápida
            valor = float(valor_texto.replace(',', '.'))
            print(f"✅ [SUCESSO] {nome_log} encontrou: {valor}")
            
        except Exception as e:
            print(f"⚠️ Erro ao achar Span direto. Tentando busca por texto no container...")
            # Backup: tenta achar qualquer div que contenha o texto e pega o número nela
            container = driver.find_element(By.XPATH, "//div[contains(., 'Total de finalizações por jogo')]")
            texto = container.text
            # Pega apenas os números e pontos/vírgulas do final da string
            valor_extraido = re.findall(r"(\d+[\.,]\d+)", texto)[-1]
            valor = float(valor_extraido.replace(',', '.'))
            print(f"✅ [SUCESSO BACKUP] {nome_log}: {valor}")

        driver.get(url_confronto)
        time.sleep(5)
        return valor

    except Exception as e:
        print(f"❌ [FALHA TOTAL] {nome_log}: {str(e)[:50]}")
        driver.get(url_confronto)
        return 0

def executar_teste_individual():
    t1_name = "Bahia"
    t2_name = "Red Bull Bragantino"
    
    print(f"\n🚀 === INICIANDO TESTE DE RASPAGEM (BUSCA + INDIVIDUAL) === 🚀")
    
    driver = configurar_browser()
    wait = WebDriverWait(driver, 25)
    
    try:
        # [PROCESSO 1] BUSCA DO ID
        driver.get("https://www.sofascore.com/pt/")
        
        try:
            cookies = driver.find_elements(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Agree')]")
            if cookies: cookies[0].click()
        except: pass

        search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
        search_input.click()
        search_input.send_keys(f"{t1_name} {t2_name}")
        time.sleep(8)
        
        resultado_xpath = "//a[contains(@href, '/football/match/')]"
        resultados = driver.find_elements(By.XPATH, resultado_xpath)
        if not resultados:
            print("❌ Falha na busca inicial.")
            return

        url_confronto = resultados[0].get_attribute("href")
        print(f"✅ Confronto Encontrado: {url_confronto}")
        
        driver.get(url_confronto)
        time.sleep(7)

        # [PROCESSO 2] RASPAGEM INDIVIDUAL
        # Chamamos a função passando o driver, o wait e os nomes dos times
        media_casa = raspar_dados_time(driver, wait, f"//bdi[contains(text(), '{t1_name}')]", t1_name, url_confronto)
        media_fora = raspar_dados_time(driver, wait, f"//bdi[contains(text(), '{t2_name}')]", t2_name, url_confronto)

        # [PROCESSO 3] RESULTADO FINAL
        print(f"\n📊 === RESULTADO FINAL === 📊")
        if media_casa > 0 and media_fora > 0:
            media_final = (media_casa + media_fora) / 2
            print(f"🎯 Média {t1_name}: {media_casa} | Média {t2_name}: {media_fora}")
            print(f"📈 Resultado Combinado: {media_final:.2f}")
            
            if media_final > 10.5:
                print("✅ APROVADO PARA ENTRADA (> 10.5)")
            else:
                print("⚠️ REJEITADO (Abaixo da média)")
        else:
            print("❌ Falha ao obter uma ou ambas as médias.")

    except Exception as e:
        print(f"❌ Erro Mestre: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    executar_teste_individual()
