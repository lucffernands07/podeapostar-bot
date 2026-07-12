import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    # 1. Configuração do Driver igual ao ambiente de produção/Actions
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Altere para remover se quiser ver o navegador abrindo localmente
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # User-agent para evitar bloqueios bobos de renderização
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    urls_teste = {
        "CHUTES": "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/resumo/estatisticas-jogadores/finalizacoes/",
        "ATAQUE": "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/resumo/estatisticas-jogadores/ataque/"
    }
    
    print("\n🚀 INICIANDO TESTE ISOLADO DE RASPAGEM DE SCOUTS ADV\n" + "="*60)
    
    try:
        # 🎯 TESTE 1: FINALIZAÇÕES (CHUTES)
        print(f"\n[TESTE CHUTES] Navegando para: {urls_teste['CHUTES']}")
        driver.get(urls_teste["CHUTES"])
        
        # Simula rolagem e espera a inércia do JS do Flashscore
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(4.0) 
        
        # Varredura de cabeçalho para achar a coluna
        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class^='wcl-tableHeadCell_']")
        print(f"[TESTE CHUTES] Cabeçalhos encontrados na página: {len(cabecalhos_fin)}")
        
        indice_chutes = 5  
        for idx_th, th in enumerate(cabecalhos_fin):
            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
            if any(x in texto_th for x in ["ALVO", "TARGET", "NO GOL", "CHUTES", "FIN"]):
                indice_chutes = idx_th
                print(f"👉 Coluna de Chutes detectada no índice: {indice_chutes} (Texto: '{texto_th}')")
                break

        # Captura de linhas com todos os seletores possíveis
        linhas_fin = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, [class^='wcl-table__row_'], [data-testid='wcl-tableRow']")
        print(f"📊 Linhas de chutes detectadas (Seletor Direto): {len(linhas_fin)}")
        
        if len(linhas_fin) == 0:
            print("⚠️ Linhas Diretas deram 0. Tentando via Fallback de Tabela...")
            tabelas = driver.find_elements(By.CSS_SELECTOR, "[class^='wcl-table_'], table, [data-testid='wcl-table']")
            for tb in tabelas:
                linhas_fallback = tb.find_elements(By.TAG_NAME, "tr") or tb.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
                if len(linhas_fallback) > 0:
                    linhas_fin = linhas_fallback
                    print(f"✅ Fallback funcionou! Linhas encontradas: {len(linhas_fin)}")
                    break
        
        # Amostragem de dados capturados
        if len(linhas_fin) > 0:
            print("\n📋 Primeiros 3 jogadores listados na tabela de Chutes:")
            cont = 0
            for linha in linhas_fin:
                if cont >= 3: break
                try:
                    nome_el = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                    nome = driver.execute_script("return arguments[0].textContent;", nome_el).strip()
                    celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], [class^='wcl-tableBodyCell_']")
                    valor = driver.execute_script("return arguments[0].textContent;", celulas[indice_chutes]).strip() if len(celulas) > indice_chutes else "N/A"
                    print(f"   👤 Jogador: {nome} | Chutes na Coluna {indice_chutes}: {valor}")
                    cont += 1
                except:
                    continue
        else:
            print("🚨 ERRO: Não foi possível ler nenhuma linha de chute de jeito nenhum.")
            print(f"🔍 PREVIEW DO HTML INTERNO DA PÁGINA:\n{driver.page_source[:600]}")

        print("\n" + "="*60)

        # 🎯 TESTE 2: ATAQUE (FALTAS SOFRIDAS)
        print(f"\n[TESTE ATAQUE] Navegando para: {urls_teste['ATAQUE']}")
        driver.get(urls_teste["ATAQUE"])
        
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(4.0)
        
        cabecalhos_atq = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class^='wcl-tableHeadCell_']")
        print(f"[TESTE ATAQUE] Cabeçalhos encontrados na página: {len(cabecalhos_atq)}")
        
        indice_faltas = 5  
        for idx_th, th in enumerate(cabecalhos_atq):
            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
            if any(x in texto_th for x in ["SOFRIDAS", "FALTAS SOFRIDAS", "FOULS SUFFERED", "FS"]):
                indice_faltas = idx_th
                print(f"👉 Coluna de Faltas detectada no índice: {indice_faltas} (Texto: '{texto_th}')")
                break

        linhas_atq = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, [class^='wcl-table__row_'], [data-testid='wcl-tableRow']")
        print(f"📊 Linhas de ataque detectadas (Seletor Direto): {len(linhas_atq)}")
        
        if len(linhas_atq) == 0:
            print("⚠️ Linhas Diretas deram 0. Tentando via Fallback de Tabela...")
            tabelas = driver.find_elements(By.CSS_SELECTOR, "[class^='wcl-table_'], table, [data-testid='wcl-table']")
            for tb in tabelas:
                linhas_fallback = tb.find_elements(By.TAG_NAME, "tr") or tb.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
                if len(linhas_fallback) > 0:
                    linhas_atq = linhas_fallback
                    print(f"✅ Fallback funcionou! Linhas encontradas: {len(linhas_atq)}")
                    break
                    
        if len(linhas_atq) > 0:
            print("\n📋 Primeiros 3 jogadores listados na tabela de Faltas Sofridas:")
            cont = 0
            for linha in linhas_atq:
                if cont >= 3: break
                try:
                    nome_el = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                    nome = driver.execute_script("return arguments[0].textContent;", nome_el).strip()
                    celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], [class^='wcl-tableBodyCell_']")
                    valor = driver.execute_script("return arguments[0].textContent;", celulas[indice_faltas]).strip() if len(celulas) > indice_faltas else "N/A"
                    print(f"   👤 Jogador: {nome} | Faltas col {indice_faltas}: {valor}")
                    cont += 1
                except:
                    continue
        else:
            print("🚨 ERRO: Não foi possível ler nenhuma linha de falta de jeito nenhum.")
            print(f"🔍 PREVIEW DO HTML INTERNO DA PÁGINA:\n{driver.page_source[:600]}")

    except Exception as e:
        print(f"\n❌ Erro crítico na execução do teste: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_isolado()
                                           
