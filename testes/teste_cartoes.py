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
    try:
        # LOG REQUISITO 2 e 3: Mostra qual jogo específico está abrindo para analisar cartões
        print(f"      🌍 [Navegação] Abrindo jogo: {url_jogo}")
        driver.get(url_jogo)
        
        # Garante o carregamento dos elementos reais de estatísticas antes da leitura
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-statistics-value']")))
        time.sleep(2) 
        
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics']")
        print(f"      🔍 [DOM] Encontradas {len(linhas)} linhas estruturais de estatísticas.")
        
        for linha in linhas:
            try:
                cat_el = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-statistics-category']")
                texto_categoria = cat_el.text.upper().strip()
                
                if "CARTÕES AMARELOS" in texto_categoria or "CARTÃO AMARELO" in texto_categoria:
                    valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics-value']")
                    
                    if len(valores) >= 2:
                        txt_casa = valores[0].text.strip()
                        txt_fora = valores[1].text.strip()
                        
                        val_casa = int(txt_casa) if txt_casa.isdigit() else 0
                        val_fora = int(txt_fora) if txt_fora.isdigit() else 0
                        
                        return val_casa if buscar_casa else val_fora
            except:
                continue
                
        print("      ⚠️ [Aviso] Texto 'Cartões amarelos' não foi achado nas estatísticas deste jogo.")
    except Exception as e:
        print(f"      ❌ [Erro] Falha ao ler a estrutura do DevTools: {e}")
    return 0
    
def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    # Confronto atualizado conforme solicitado: Brasil x Haiti (H2H Total)
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/haiti-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE INDESTRUTÍVEL] ANÁLISE DE CARTÕES COMPLETA")
    print("="*60 + "\n")
    
    # LOG REQUISITO 1: URL H2H Principal do Confronto
    print(f"🔗 Acessando página H2H principal: {url_inicial}\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # --- TABELA 1: MANDANTE (CASA) ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_mandante = []
        for linha in linhas_t1:
            try:
                id_attr = linha.get_attribute("id") or ""
                if not id_attr:
                    link_el = linha.find_element(By.TAG_NAME, "a")
                    id_attr = link_el.get_attribute("id") or link_el.get_attribute("href") or ""
                
                match = re.search(r'g_1_([A-Za-z0-9]+)', id_attr) or re.search(r'/jogo/([^/]+)', id_attr)
                id_jogo = match.group(1) if match else (id_attr.split('_')[-1] if "_" in id_attr else None)
                
                if id_jogo:
                    urls_mandante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas/total/")
            except:
                continue

        # LOG REQUISITO 2: URL dos 3 últimos jogos da Casa
        print(f"📋 URLs geradas para o Mandante: {urls_mandante}")

        # Processa e busca cartões da Casa
        for idx, url in enumerate(urls_mandante):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            # LOG REQUISITO 3: Total do jogo individual
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes_t2 = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t2 = secoes_t2[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_visitante = []
        for linha in linhas_t2:
            try:
                id_attr = linha.get_attribute("id") or ""
                if not id_attr:
                    link_el = linha.find_element(By.TAG_NAME, "a")
                    id_attr = link_el.get_attribute("id") or link_el.get_attribute("href") or ""
                
                match = re.search(r'g_1_([A-Za-z0-9]+)', id_attr) or re.search(r'/jogo/([^/]+)', id_attr)
                id_jogo = match.group(1) if match else (id_attr.split('_')[-1] if "_" in id_attr else None)
                
                if id_jogo:
                    urls_visitante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas/total/")
            except:
                continue

        # LOG REQUISITO 2: URL dos 3 últimos jogos do Visitante
        print(f"📋 URLs geradas para o Visitante: {urls_visitante}")

        # Processa e busca cartões do Visitante
        for idx, url in enumerate(urls_visitante):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            # LOG REQUISITO 3: Total do jogo individual
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- EXIBIÇÃO DOS RESULTADOS FINAIS ---
        print("\n" + "="*60)
        print("📊 RESULTADO DO CONFRONTO")
        print("="*60)
        # LOG REQUISITO 3: Total consolidado em array
        print(f"🟨 Lista Mandante: {historico_mandante}")
        print(f"🟨 Lista Visitante: {historico_visitante}")

    except Exception as e:
        print(f"\n❌ Erro no fluxo de execução: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_analise_cartoes()
