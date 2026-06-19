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

def extrair_cartoes_do_jogo(driver, wait, url_jogo, buscar_casa):
    """
    Navega diretamente para a URL de resumo do jogo e extrai os cartões usando Regex,
    printando o log detalhado de cada etapa no terminal.
    """
    try:
        url_resumo = url_jogo.split("?")[0].strip("/") + "/resumo/"
        print(f"      🌍 [Navegação] Abrindo jogo: {url_resumo}")
        driver.get(url_resumo)
        time.sleep(3) # Tempo para garantir a renderização no ambiente headless
        
        # Procura linhas estruturais de estatísticas
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='category'], [class*='category_']")
        print(f"      🔍 [DOM] Encontradas {len(linhas)} linhas de categorias na página.")
        
        for linha in linhas:
            html_interno = linha.get_attribute("innerHTML")
            texto_puro = re.sub(r'<[^>]+>', ' ', html_interno).upper()
            
            if "CARTÕES AMARELOS" in texto_puro or "CARTÃO AMARELO" in texto_puro:
                print(f"      🟨 [Match] Linha de cartões localizada!")
                print(f"      📄 [HTML Bruto]: {html_interno.strip()}")
                
                # Procura números delimitados por tags ou texto limpo
                numeros = re.findall(r'>\s*(\d+)\s*<', html_interno)
                if not numeros:
                    numeros = re.findall(r'\d+', texto_puro)
                
                print(f"      📊 [Regex] Números identificados na linha: {numeros}")
                
                if len(numeros) >= 2:
                    val_casa = int(numeros[0])
                    val_fora = int(numeros[-1])
                    print(f"      ✅ [Resultado] Casa: {val_casa} | Visitante: {val_fora}")
                    return val_casa if buscar_casa else val_fora
                    
        print("      ⚠️ [Aviso] Nenhuma linha com o texto 'Cartões amarelos' foi encontrada neste jogo.")
    except Exception as e:
        print(f"      ❌ [Erro] Falha crítica ao processar a página: {e}")
    return 0

def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*80)
    print("🚀 [TESTE COM LOG DETALHADO] ANÁLISE DE CARTÕES - BRASIL X MARROCOS")
    print("="*80 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        print(f"🔗 Acessando página H2H principal: {url_inicial}")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # --- TABELA 1: MANDANTE ---
        print("\n📦 [TABELA 1] Mapeando os últimos 3 jogos do Mandante...")
        # Alvo explícito via nth-of-type(1) para evitar vazamento do DOM
        secao_mandante = driver.find_element(By.CSS_SELECTOR, ".h2h__section:nth-of-type(1)")
        linhas_t1 = secao_mandante.find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_mandante = []
        for linha in linhas_t1:
            id_attr = linha.get_attribute("id") or ""
            if "_" in id_attr:
                id_jogo = id_attr.split('_')[-1]
                urls_mandante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")
        
        print(f"📋 URLs geradas para o Mandante: {urls_mandante}")
        
        for idx, url in enumerate(urls_mandante):
            print(f"\n   ➔ [Tabela 1] Iniciando Processamento do Jogo {idx+1}/{len(urls_mandante)}")
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"   🔹 Fim do Jogo {idx+1}. Registrado para a Casa: {cartoes} cartões")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 [TABELA 2] Mapeando os últimos 3 jogos do Visitante...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Alvo explícito via nth-of-type(2) focado estritamente na segunda tabela (Visitante)
        secao_visitante = driver.find_element(By.CSS_SELECTOR, ".h2h__section:nth-of-type(2)")
        linhas_t2 = secao_visitante.find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_visitante = []
        for linha in linhas_t2:
            id_attr = linha.get_attribute("id") or ""
            if "_" in id_attr:
                id_jogo = id_attr.split('_')[-1]
                urls_visitante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")
                
        print(f"📋 URLs geradas para o Visitante: {urls_visitante}")

        for idx, url in enumerate(urls_visitante):
            print(f"\n   ➔ [Tabela 2] Iniciando Processamento do Jogo {idx+1}/{len(urls_visitante)}")
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"   🔹 Fim do Jogo {idx+1}. Registrado para o Visitante: {cartoes} cartões")

        # --- EXIBIÇÃO DOS RESULTADOS CONSOLIDADOS ---
        print("\n" + "="*80)
        print("📊 RESUMO FINAL DOS ARRAYS DO CONFRONTO")
        print("="*80)
        print(f"🟨 Lista Final Mandante (Tabela 1): {historico_mandante}")
        print(f"🟨 Lista Final Visitante (Tabela 2): {historico_visitante}")

    except Exception as e:
        print(f"\n❌ Erro geral durante o fluxo: {e}")
    finally:
        driver.quit()
        print("\n🏁 Processo de teste encerrado.")

if __name__ == "__main__":
    testar_analise_cartoes()
