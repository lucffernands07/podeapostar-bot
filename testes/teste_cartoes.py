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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def extrair_cartoes_do_jogo(driver, wait, url_jogo, buscar_casa):
    """
    Navega para a aba GERAIS de estatísticas de jogadores e extrai a soma 
    de cartões baseando-se nas últimas colunas da direita (varredura de trás para frente).
    """
    try:
        url_limpa = url_jogo.split("?")[0].strip("/")
        if "/resumo" in url_limpa:
            url_limpa = url_limpa.split("/resumo")[0]
            
        url_estatisticas = f"{url_limpa}/resumo/estatisticas-jogadores/gerais/"
        print(f"      🌍 [Navegação] Abrindo estatísticas gerais de jogadores: {url_estatisticas}")
        driver.get(url_estatisticas)
        
        # Aguarda carregar os nomes dos jogadores usando a classe nova detectada
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fp-playerName_E6lgN")))
        time.sleep(1.5)
        
        # Coleta as tabelas do framework atualizado do Flashscore
        tabelas_times = driver.find_elements(By.CSS_SELECTOR, ".wcl-table_") or driver.find_elements(By.TAG_NAME, "table")
        
        if len(tabelas_times) < 2:
            print("      ⚠️ [Aviso] Tabelas separadas não encontradas. Analisando estrutura unificada.")
            tabela_alvo = tabelas_times[0] if len(tabelas_times) > 0 else driver
        else:
            # Define se varre o Mandante (0) ou Visitante (1)
            tabela_alvo = tabelas_times[0] if buscar_casa else tabelas_times[1]
        
        linhas_jogadores = tabela_alvo.find_elements(By.CSS_SELECTOR, ".wcl-table__row_") or tabela_alvo.find_elements(By.TAG_NAME, "tr")
        
        total_amarelos = 0
        total_vermelhos = 0
        
        for linha in linhas_jogadores:
            try:
                if not linha.find_elements(By.CSS_SELECTOR, ".fp-playerName_E6lgN"):
                    continue
                    
                celulas = linha.find_elements(By.CSS_SELECTOR, ".wcl-table__bodyCell_") or linha.find_elements(By.TAG_NAME, "td")
                
                # LÓGICA DO MAIN: Lê de trás para frente usando índices negativos (-2 e -1)
                if len(celulas) >= 2:
                    txt_amarelo = driver.execute_script("return arguments[0].textContent;", celulas[-2]).strip()
                    txt_vermelho = driver.execute_script("return arguments[0].textContent;", celulas[-1]).strip()
                    
                    total_amarelos += int(txt_amarelo) if txt_amarelo.isdigit() else 0
                    total_vermelhos += int(txt_vermelho) if txt_vermelho.isdigit() else 0
            except:
                continue
                
        total_cartoes_time = total_amarelos + total_vermelhos
        tipo_time = "Casa" if buscar_casa else "Visitante"
        print(f"      ✅ [Resultado {tipo_time}] Amarelos: {total_amarelos} | Vermelhos: {total_vermelhos} | Total: {total_cartoes_time}")
        
        return total_cartoes_time

    except Exception as e:
        print(f"      ❌ [Erro] Falha ao ler a tabela de jogadores: {e}")
    return 0
    
def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE INDESTRUTÍVEL] ANÁLISE DE CARTÕES VIA CLIQUE E ABAS GERAIS")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        # --- TABELA 1: MANDANTE ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_mandante = []
        # Captura as URLs completas de forma nativa abrindo o link temporariamente
        for linha in linhas_t1:
            try:
                driver.execute_script("arguments[0].click();", linha)
                time.sleep(1.5)
                driver.switch_to.window(driver.window_handles[-1])
                
                url_completa = driver.current_url.split("?")[0].strip("/")
                urls_mandante.append(url_completa)
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                continue

        for idx, url in enumerate(urls_mandante):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões acumulados pelo time")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_visitante = []
        for linha in linhas_t2:
            try:
                driver.execute_script("arguments[0].click();", linha)
                time.sleep(1.5)
                driver.switch_to.window(driver.window_handles[-1])
                
                url_completa = driver.current_url.split("?")[0].strip("/")
                urls_visitante.append(url_completa)
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                continue

        for idx, url in enumerate(urls_visitante):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões acumulados pelo time")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        print("\n" + "="*60)
        print("📊 RESULTADO DO CONFRONTO (SOMA DAS ABAS GERAIS)")
        print("="*60)
        print(f"🟨 Lista Mandante: {historico_mandante}")
        print(f"🟨 Lista Visitante: {historico_visitante}")
        
        total_cartoes = sum(historico_mandante) + sum(historico_visitante)
        media_6_jogos = total_cartoes / 6
        
        print(f"\n📊 Média de cartões (6 jogos combinados): {media_6_jogos:.2f}")
        if media_6_jogos < 2.5:
            print("   💡 Tendência: -2.5 cartões")
        else:
            print("   💡 Tendência: +2.5 cartões")

    except Exception as e:
        print(f"\n❌ Erro no fluxo de execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
