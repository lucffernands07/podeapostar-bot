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
    Extrai os cartões amarelos diretamente da tela de estatísticas/destaques ativa,
    varrendo todas as linhas de categorias disponíveis de forma resiliente.
    """
    try:
        # Garante que estamos na aba de resumo/estatísticas do jogo
        url_jogo_base = driver.current_url.split("?")[0].strip("/")
        if "/resumo" not in driver.current_url:
            driver.get(url_jogo_base + "/resumo/")
            time.sleep(2)

        # Espera carregar qualquer elemento de categoria ou cabeçalho de destaques
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='category_'], [class*='stat__header']")))
        
        # Estratégia de Varredura Ampla: Pegamos todas as linhas de categorias textuais da tela
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='category'], [class*='category_']")
        
        for linha in linhas:
            texto_linha = linha.text.upper()
            
            if "CARTÕES AMARELOS" in texto_linha or "CARTÃO AMARELO" in texto_linha:
                # Extrai todos os elementos de texto internos da linha
                elementos_internos = linha.find_elements(By.XPATH, ".//*")
                textos_limpos = [el.text.strip() for el in elementos_internos if el.text.strip()]
                
                # Exemplo esperado de textos_limpos do seu print: ['1', 'Cartões amarelos', '3']
                # Remove duplicatas consecutivas mantendo a ordem para evitar ruído no DOM
                textos_filtrados = []
                for t in textos_limpos:
                    if not textos_filtrados or t != textos_filtrados[-1]:
                        textos_filtrados.append(t)
                
                # Procura a posição da palavra-chave na lista limpa
                for idx, item in enumerate(textos_filtrados):
                    if "CARTÃO" in item.upper() or "CARTÕES" in item.upper():
                        try:
                            txt_casa = textos_filtrados[idx - 1]
                            txt_fora = textos_filtrados[idx + 1]
                            
                            val_casa = int(txt_casa) if txt_casa.isdigit() else 0
                            val_fora = int(txt_fora) if txt_fora.isdigit() else 0
                            
                            return val_casa if buscar_casa else val_fora
                        except:
                            continue
    except Exception as e:
        print(f"     ⚠️ Erro ao buscar elemento de cartões: {e}")
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
    
