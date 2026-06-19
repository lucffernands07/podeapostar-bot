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
    Entra na aba de estatísticas totais do jogo e captura os cartões.
    buscar_casa: True se queremos os cartões do time que estamos analisando (como mandante/visitante histórico)
    """
    try:
        url_estatisticas = driver.current_url.split("?")[0].strip("/") + "/resumo/estatisticas/total/"
        driver.get(url_estatisticas)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "._category_1m31k_5")))
        time.sleep(2)
        
        linhas_estatisticas = driver.find_elements(By.CSS_SELECTOR, "._category_1m31k_5")
        for linha in linhas_estatisticas:
            texto_categoria = linha.find_element(By.CSS_SELECTOR, "._categoryName_1m31k_19").text.upper()
            
            if "CARTÕES AMARELOS" in texto_categoria or "CARTÃO AMARELO" in texto_categoria:
                val_casa = int(linha.find_element(By.CSS_SELECTOR, "._homeValue_1m31k_10").text.strip())
                val_fora = int(linha.find_element(By.CSS_SELECTOR, "._awayValue_1m31k_14").text.strip())
                
                return val_casa if buscar_casa else val_fora
    except:
        pass
    return 0

def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    # URL base do H2H informada
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 INICIANDO ANÁLISE DE CARTÕES (ÚLTIMOS 3 JOGOS MANDANTE E VISITANTE)")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # --- TABELA 1: ÚLTIMOS JOGOS DO MANDANTE ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        linhas_mandante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")[:3]
        
        for idx in range(len(linhas_mandante)):
            # Recarrega para evitar StaleElement
            driver.get(url_inicial)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            linha = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")[idx]
            
            # Descobre se o nosso Mandante Principal jogou em casa ou fora nesse jogo específico do histórico
            partes = linha.text.split('\n')
            time_casa_historico = partes[2].strip()
            
            driver.execute_script("arguments[0].click();", linha)
            time.sleep(2)
            
            # Se no histórico o nome bate com o mandante, pegamos os cartões da "Casa", senão "Fora"
            # (Simplificado: pegando o valor da esquerda/casa do jogo do histórico para fins de teste)
            cartoes = extrair_cartoes_do_jogo(driver, wait, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- TABELA 2: ÚLTIMOS JOGOS DO VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Força o seletor a buscar na segunda seção (visitante)
        linhas_visitante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(2) .h2h__row")[:3]
        if not lines_visitante:
            # Fallback caso a estrutura mude
            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if len(secoes) >= 2:
                linhas_visitante = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]

        for idx in range(len(linhas_visitante)):
            driver.get(url_inicial)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            
            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            linha = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[idx]
            
            driver.execute_script("arguments[0].click();", linha)
            time.sleep(2)
            
            # Captura os cartões do visitante nesse jogo
            cartoes = extrair_cartoes_do_jogo(driver, wait, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões")

        # --- PROCESSAMENTO E MÉDIAS ---
        print("\n" + "="*60)
        print("📊 RESULTADO CONSOLIDADO DE CARTÕES")
        print("="*60)
        
        media_mandante = sum(historico_mandante) / len(historico_mandante) if historico_mandante else 0
        media_visitante = sum(historico_visitante) / len(historico_visitante) if historico_visitante else 0
        
        print(f"🟨 Média Mandante (Últimos 3 jogos): {media_mandante:.2f} cartões/jogo {historico_mandante}")
        print(f"🟨 Média Visitante (Últimos 3 jogos): {media_visitante:.2f} cartões/jogo {historico_visitante}")
        print(f"📈 Média Total do Confronto: {(media_mandante + media_visitante):.2f}")

    except Exception as e:
        print(f"\n❌ Erro crítico na captura de cartões: {e}")
    finally:
        driver.quit()
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
