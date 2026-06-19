import os
import sys
import time
import re
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

def extrair_cartoes_do_jogo(driver, wait, buscar_casa):
    """
    Extrai os cartões amarelos usando Expressão Regular diretamente no innerHTML,
    ignorando variações de elementos internos ou spans do FlashScore.
    """
    try:
        # Força estar na aba resumo do jogo ativo
        url_jogo_base = driver.current_url.split("?")[0].strip("/")
        if "/resumo" not in driver.current_url:
            driver.get(url_jogo_base + "/resumo/")
            time.sleep(2)

        # Aguarda carregar qualquer linha de categoria
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='category_'], [class*='stat__header']")))
        
        # Pega todas as linhas de categorias textuais disponíveis
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='category'], [class*='category_']")
        
        for linha in linhas:
            # Captura o HTML inteiro dessa linha específica
            html_interno = linha.get_attribute("innerHTML")
            
            # Remove tags HTML para testar se a linha é de cartões
            texto_puro = re.sub(r'<[^>]+>', ' ', html_interno).upper()
            
            if "CARTÕES AMARELOS" in texto_puro or "CARTÃO AMARELO" in texto_puro:
                # O FlashScore coloca os números dentro de tags como >2< ou >0<. 
                # Esta regex captura todos os números isolados dentro do HTML daquela linha
                numeros = re.findall(r'>\s*(\d+)\s*<', html_interno)
                
                # Se não achar com os delimitadores de tag, busca números gerais na linha desmascarada
                if not numeros:
                    numeros = re.findall(r'\d+', texto_puro)
                
                # Uma linha de estatística válida precisa ter pelo menos 2 números (casa e visitante)
                if len(numeros) >= 2:
                    val_casa = int(numeros[0])
                    val_fora = int(numeros[-1]) # Pega o último elemento para evitar ruídos de IDs/classes
                    
                    return val_casa if buscar_casa else val_fora
                    
    except Exception as e:
        print(f"     ⚠️ Erro crítico Regex ao ler cartões: {e}")
    return 0


def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE] ANÁLISE DE CARTÕES COMPLETA (MANDANTE E VISITANTE)")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # --- TABELA 1: MANDANTE ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        for idx in range(len(linhas_t1)):
            if idx > 0:
                driver.get(url_inicial)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
                linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            linha = linhas_t1[idx]
            driver.execute_script("arguments[0].click();", linha)
            time.sleep(2.5)
            
            # Captura o valor correspondente à casa na tabela 1
            cartoes = extrair_cartoes_do_jogo(driver, wait, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        for idx in range(len(linhas_t2)):
            if idx > 0:
                driver.get(url_inicial)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
                linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            linha = linhas_t2[idx]
            driver.execute_script("arguments[0].click();", linha)
            time.sleep(2.5)
            
            # Captura o valor correspondente ao visitante na tabela 2
            cartoes = extrair_cartoes_do_jogo(driver, wait, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        print("\n" + "="*60)
        print("📊 RESULTADO DO CONFRONTO")
        print("="*60)
        print(f"🟨 Lista Mandante: {historico_mandante}")
        print(f"🟨 Lista Visitante: {historico_visitante}")

    except Exception as e:
        print(f"\n❌ Erro no fluxo de execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
    
