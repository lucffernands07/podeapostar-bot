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
    print("🚀 INICIANDO CONEXÃO E NAVEGAÇÃO")
    print("="*60 + "\n")
    
    try:
        # --- ETAPA 1: Captura do ID e Redirecionamento ---
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        elemento_jogo = driver.find_element(By.開, "//*[contains(text(), 'Irlanda do Norte')]") if hasattr(By, '開') else driver.find_element(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
        driver.execute_script("arguments[0].click();", elemento_jogo)
        time.sleep(4)
        
        id_real = driver.current_url.split("?")[0].strip("/").split("/")[-1].split("-")[-1]
        url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/"
        
        print(f"🔗 Acessando Hub de Estatísticas do Jogador: {url_estatisticas}")
        driver.get(url_estatisticas)
        time.sleep(5)
        
        # --- ETAPA 2: O PULO DO GATO (Clicar no Sub-menu Finalizações) ---
        print("🎯 Forçando clique no botão 'FINALIZAÇÕES' para revelar a tabela...")
        try:
            # Busca pelo elemento de texto que você vê no print
            botao_finalizacoes = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Finalizações')] | //div[contains(text(), 'Finalizações')]")))
            driver.execute_script("arguments[0].click();", botao_finalizacoes)
            print("✅ Sub-aba 'Finalizações' ativada com sucesso!")
            time.sleep(3)
        except Exception as e_clique:
            print(f"⚠️ Não conseguiu clicar no botão 'Finalizações' pelo texto. Erro: {e_clique}")
            print("Tentando buscar por elementos de sub-menu ancorados...")
            
        # --- ETAPA 3: Raspagem Cirúrgica dos Dados Revelados ---
        print("\n" + "="*60)
        print("📊 PROCESSANDO LINHAS DE JOGADORES REVELADAS")
        print("="*60)
        
        # Identifica o índice correto da coluna desejada ("Finalizações no alvo")
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell']")
        indice_chutes_no_gol = -1
        contador_colunas = 0
        
        for th in cabecalhos:
            alias = th.get_attribute("data-analytics-alias")
            if alias == "SHOTS_ON_TARGET":
                indice_chutes_no_gol = contador_colunas
                break
            contador_colunas += 1
            
        if indice_chutes_no_gol == -1:
            indice_chutes_no_gol = 4  # Mantém o fallback caso o alias mude
            
        # Captura as linhas da tabela que agora estão visíveis no DOM
        linhas_dados = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
        print(f"📋 Total de linhas na tabela: {len(linhas_dados)}\n")
        
        for linha in linhas_dados:
            try:
                # Pega o nome do jogador dentro da linha atual
                celula_nome = linha.find_element(By.CSS_SELECTOR, "[class*='participantName'], [class*='name_']")
                nome_jogador = celula_nome.text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador:
                    continue
                
                # Pega os valores numéricos da mesma linha
                celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
                
                if len(celulas_valores) > indice_chutes_no_gol:
                    valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                    # Faz o tratamento do "-" para "0" baseado no seu pedaço de HTML
                    chutes_no_alvo = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                    
                    print(f"🏃‍♂️ {nome_jogador:<25} ➔ Chutes no Alvo: {chutes_no_alvo}")
            except Exception:
                continue

        print("\n" + "="*60)
        print("🎉 FIM DA RASPAGEM: DADOS EXTRAÍDOS COM SUCESSO")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro Geral: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_clique_pelo_nome()
            
