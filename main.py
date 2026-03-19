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
        print(f"[LOG] Passo 1: Clicando no time {nome_log} no H2H...")
        # Localiza o <bdi> ou o link do time e clica
        btn_time = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_clique_time)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_time)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", btn_time)
        
        print(f"[LOG] Passo 2: Clicando na aba 'Estatísticas'...")
        # Usa o seletor <a> que você passou originalmente
        btn_stats = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab:statistics']")))
        driver.execute_script("arguments[0].click();", btn_stats)
        
        print(f"[LOG] Passo 3: Aguardando renderização do Grid (10s)...")
        time.sleep(10)
        driver.execute_script("window.scrollBy(0, 500);")

        # --- LÓGICA DO CARD ATACANDO ---
        # Verificamos se o texto 'Total de finalizações por jogo' já está no DOM
        conteudo_atual = driver.find_element(By.TAG_NAME, "main").text
        
        if "Total de finalizações por jogo" not in conteudo_atual:
            print(f"[LOG] Dado não visível. Tentando expandir card 'Atacando'...")
            # Clica no Span/Div do card 'Atacando' para abrir
            try:
                card_atacando = driver.find_element(By.XPATH, "//span[contains(text(), 'Atacando')] | //div[contains(., 'Atacando') and contains(@class, 'jc_space-between')]")
                driver.execute_script("arguments[0].click();", card_atacando)
                time.sleep(4)
                conteudo_atual = driver.find_element(By.TAG_NAME, "main").text
            except:
                print("⚠️ Não foi possível clicar no card Atacando.")

        # --- EXTRAÇÃO FINAL ---
        print(f"[LOG] Passo 4: Buscando valor numérico...")
        # Regex idêntica à de escanteios: busca a frase e captura o número decimal à frente
        busca = re.search(r"Total de finalizações por jogo\s*(\d+[\.,]\d+)", conteudo_atual, re.IGNORECASE)
        
        if busca:
            valor = float(busca.group(1).replace(',', '.'))
            print(f"✅ [SUCESSO] {nome_log}: {valor}")
        else:
            print(f"❌ [FALHA] Não encontrou o valor após expandir/verificar.")
            valor = 0

        # Volta para a página do jogo para o próximo time (Bahia -> Jogo -> Bragantino)
        driver.execute_script("window.history.go(-1);") # Volta das Stats para o Perfil
        time.sleep(3)
        driver.execute_script("window.history.go(-1);") # Volta do Perfil para o Jogo
        time.sleep(5)
        return valor

    except Exception as e:
        print(f"❌ [ERRO] Falha no fluxo de {nome_log}: {str(e)[:50]}")
        driver.get(url_confronto) # Reset de segurança
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
                      
