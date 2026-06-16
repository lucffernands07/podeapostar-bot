import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def testar_clique_pelo_nome():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    print("\n" + "="*60)
    print("🚀 INICIANDO CLIQUE DIRETO NO TEXTO DO JOGO")
    print("="*60 + "\n")
    
    try:
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        elemento_jogo = driver.find_element(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
        
        print("🔄 Clicando na partida da Irlanda do Norte...")
        driver.execute_script("arguments[0].click();", elemento_jogo)
        
        time.sleep(5)
        
        url_final = driver.current_url
        print(f"🔗 URL capturada após o clique: {url_final}")
        
        # --- Nova lógica de extração sem erro de alvo ---
        url_limpa = url_final.split("?")[0]
        partes_url = url_limpa.strip("/").split("/")
        ultimo_bloco = partes_url[-1] 
        id_real = ultimo_bloco.split("-")[-1]
        
        url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"\n3. ✅ URL ALVO FORMATADA: {url_estatisticas}")
        # ------------------------------------------------
        
        print("\n🔀 Redirecionando para validar acesso à página alvo...")
        driver.get(url_estatisticas)
        time.sleep(5)
        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: PRONTO PARA A RASPAGEM")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_clique_pelo_nome()
        
