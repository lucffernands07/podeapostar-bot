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
    Navega diretamente para a URL de resumo do jogo e extrai os cartões usando Regex.
    """
    try:
        url_resumo = url_jogo.split("?")[0].strip("/") + "/resumo/"
        driver.get(url_resumo)
        time.sleep(3) # Tempo extra para o DOM renderizar no GitHub Actions
        
        # Procura qualquer linha estrutural de estatísticas
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='category'], [class*='category_']")
        
        for linha in linhas:
            html_interno = linha.get_attribute("innerHTML")
            texto_puro = re.sub(r'<[^>]+>', ' ', html_interno).upper()
            
            if "CARTÕES AMARELOS" in texto_puro or "CARTÃO AMARELO" in texto_puro:
                numeros = re.findall(r'>\s*(\d+)\s*<', html_interno)
                if not numeros:
                    numeros = re.findall(r'\d+', texto_puro)
                
                if len(numeros) >= 2:
                    val_casa = int(numeros[0])
                    val_fora = int(numeros[-1])
                    return val_casa if buscar_casa else val_fora
    except Exception as e:
        print(f"     ⚠️ Erro ao processar URL {url_jogo}: {e}")
    return 0

def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE INDESTRUTÍVEL] ANÁLISE DE CARTÕES COMPLETA")
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
        
        urls_mandante = []
        for linha in linhas_t1:
            # Captura o ID estrutural do jogo ou o link nativo do FlashScore se houver
            try:
                # O FlashScore costuma colocar atributos ou links clicáveis internos com a classe ou tag 'a'
                link_el = linha.find_element(By.TAG_NAME, "a") if linha.find_elements(By.TAG_NAME, "a") else linha
                href = link_el.get_attribute("href") or link_el.get_attribute("data-url")
                if href:
                    urls_mandante.append(href)
            except:
                continue

        # Se falhar em pegar a URL direta pelo href, montamos usando o ID padrão igual no main.py
        if not urls_mandante:
            for linha in linhas_t1:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_mandante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")

        # Processa as URLs coletadas do Mandante
        for idx, url in enumerate(urls_mandante[:3]):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_visitante = []
        for linha in linhas_t2:
            try:
                link_el = linha.find_element(By.TAG_NAME, "a") if linha.find_elements(By.TAG_NAME, "a") else linha
                href = link_el.get_attribute("href") or link_el.get_attribute("data-url")
                if href:
                    urls_visitante.append(href)
            except:
                continue

        if not urls_visitante:
            for linha in linhas_t2:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_visitante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")

        # Processa as URLs coletadas do Visitante
        for idx, url in enumerate(urls_visitante[:3]):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=False)
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
