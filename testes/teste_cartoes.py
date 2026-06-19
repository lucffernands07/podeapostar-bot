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
    Navega para a aba de estatísticas totais e extrai os cartões 
    garantindo a captura dos elementos internos da categoria.
    """
    try:
        url_estatisticas = driver.current_url.split("?")[0].strip("/") + "/resumo/estatisticas/total/"
        driver.get(url_estatisticas)
        
        # Espera carregar a categoria principal
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-statistics-category']")))
        time.sleep(2)
        
        # Pega todas as linhas de categorias da página
        linhas_estatisticas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics-category']")
        
        for linha in linhas_estatisticas:
            # Buscamos todos os spans (ou elementos de texto) contidos nessa linha de categoria
            elementos_texto = linha.find_elements(By.XPATH, ".//span")
            
            # Se não achar por span, tenta buscar todas as tags filhas diretas
            if len(elementos_texto) < 3:
                elementos_texto = linha.find_elements(By.XPATH, "./*")

            # Tratando a estrutura padrão do FlashScore de 3 colunas: [Valor_Casa, Nome_Categoria, Valor_Fora]
            if len(elementos_texto) >= 3:
                texto_categoria = elementos_texto[1].text.upper()  # O do meio sempre é o nome
                
                if "CARTÕES AMARELOS" in texto_categoria or "CARTÃO AMARELO" in texto_categoria:
                    txt_casa = elementos_texto[0].text.strip()
                    txt_fora = elementos_texto[2].text.strip()
                    
                    # Garante que são números válidos para não quebrar no int() caso venha string vazia ou hífen
                    val_casa = int(txt_casa) if txt_casa.isdigit() else 0
                    val_fora = int(txt_fora) if txt_fora.isdigit() else 0
                    
                    return val_casa if buscar_casa else val_fora
    except Exception as e:
        print(f"     ⚠️ Erro ao ler cartões nesta URL: {e}")
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
    
