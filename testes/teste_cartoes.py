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
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def extrair_cartoes_do_jogo(driver, url_jogo, buscar_casa):
    """
    Abre o jogo em uma nova aba, extrai os cartões com base na estrutura 
    do FlashScore e retorna o valor inteiro.
    """
    # Abre uma nova aba para o jogo específico seguindo o padrão do seu main.py
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    val_cartoes = 0
    try:
        url_resumo = driver.current_url.split("?")[0].strip("/") + "/resumo/estatisticas/"
        driver.get(url_resumo)
        time.sleep(2.5) # Tempo seguro para renderização do DOM dinâmico
        
        # Procura as linhas de estatísticas estruturais
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics']")
        
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
                        
                        val_cartoes = val_casa if buscar_casa else val_fora
                        print(f"      ✅ [Match Cartões] Casa: {val_casa} | Visitante: {val_fora} (Alvo buscado: {'Casa' if buscar_casa else 'Fora'} -> {val_cartoes})")
                        break
            except:
                continue
    except Exception as e:
        print(f"      ⚠️ Falha ao ler estatísticas do jogo {url_jogo}: {e}")
    finally:
        # Fecha a aba atual e retorna o controle para a aba principal
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
    return val_cartoes
    
def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    # URL base do confronto direto para o ambiente de testes
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE ALINHADO AO MAIN] ANÁLISE DE CARTÕES")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # --- TABELA 1: ÚLTIMOS JOGOS DO MANDANTE (idx 0) ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        urls_mandante = []
        
        for linha in linhas_t1:
            try:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_mandante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")
            except:
                continue

        for idx, url in enumerate(urls_mandante):
            print(f"   🔎 Analisando jogo {idx+1} do Mandante...")
            cartoes = extrair_cartoes_do_jogo(driver, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"   ➔ Salvo: {cartoes} cartões")

        # --- TABELA 2: ÚLTIMOS JOGOS DO VISITANTE (idx 1) ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        urls_visitante = []
        
        for linha in linhas_t2:
            try:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_visitante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}/")
            except:
                continue

        for idx, url in enumerate(urls_visitante):
            print(f"   🔎 Analisando jogo {idx+1} do Visitante...")
            cartoes = extrair_cartoes_do_jogo(driver, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"   ➔ Salvo: {cartoes} cartões")

        # --- EXIBIÇÃO CONSOLIDADA DOS RESULTADOS ---
        print("\n" + "="*60)
        print("📊 RESULTADO DO CONFRONTO COMPILADO")
        print("="*60)
        print(f"🟨 Lista Histórica Mandante (Casa): {historico_mandante}")
        print(f"🟨 Lista Histórica Visitante (Fora): {historico_visitante}")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de execução: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
