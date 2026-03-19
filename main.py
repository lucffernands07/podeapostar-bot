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
        print(f"\n[LOG] Passo 1: Clicando no time {nome_log}...")
        # Localiza o time no H2H (usa o bdi que você passou)
        btn_time = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_clique_time)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_time)
        time.sleep(3)
        driver.execute_script("arguments[0].click();", btn_time)
        
        print(f"[LOG] Passo 2: Clicando na aba 'Estatísticas'...")
        # Espera o botão da aba carregar e clica
        btn_stats = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab:statistics']")))
        driver.execute_script("arguments[0].click();", btn_stats)
        
        print(f"[LOG] Passo 3: Aguardando carregamento do Grid (12s)...")
        time.sleep(12)
        driver.execute_script("window.scrollBy(0, 500);")

        # Pega o conteúdo do main (onde estão os cards)
        try:
            conteudo_main = driver.find_element(By.TAG_NAME, "main").text
        except:
            conteudo_main = driver.find_element(By.TAG_NAME, "body").text

        # Lógica do Card: Se não achar o texto, tenta expandir o card 'Atacando'
        if "Total de finalizações por jogo" not in conteudo_main:
            print(f"[LOG] Dado não visível. Tentando abrir o card 'Atacando'...")
            try:
                card_atacando = driver.find_element(By.XPATH, "//span[contains(text(), 'Atacando')] | //div[contains(., 'Atacando')]")
                driver.execute_script("arguments[0].click();", card_atacando)
                time.sleep(5)
                conteudo_main = driver.find_element(By.TAG_NAME, "main").text
            except:
                print("⚠️ Aviso: Não foi possível clicar no card Atacando (talvez já esteja aberto).")

        # --- EXTRAÇÃO FINAL ---
        print(f"[LOG] Passo 4: Buscando valor numérico...")
        busca = re.search(r"Total de finalizações por jogo\s*(\d+[\.,]\d+)", conteudo_main, re.IGNORECASE)
        
        if busca:
            valor = float(busca.group(1).replace(',', '.'))
            print(f"✅ [SUCESSO] {nome_log}: {valor}")
        else:
            print(f"❌ [FALHA] Valor não encontrado para {nome_log}.")
            valor = 0

        # Volta para a página do jogo para o próximo time
        print(f"[LOG] Retornando ao confronto...")
        driver.get(url_confronto)
        time.sleep(5)
        return valor

    except Exception as e:
        print(f"❌ [ERRO] Falha no fluxo de {nome_log}: {str(e)[:50]}")
        driver.get(url_confronto)
        time.sleep(5)
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
