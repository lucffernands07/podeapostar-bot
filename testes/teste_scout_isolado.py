import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 12)
    
    # Passamos a URL apontando direto para a sub-seção estrutural das estatísticas
    url_jogo_base = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas-jogadores/finalizacoes"
    
    print("\n🚀 INICIANDO TESTE ISOLADO DIRETURBO COM RENDERIZAÇÃO SPA\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Abrindo jogo com âncora hash SPA: {url_jogo_base}")
        driver.get(url_jogo_base)
        time.sleep(4.0) # Tempo para o script interno do Flashscore reagir à URL
        
        # Tentativa de clique nos botões de abas usando classes exclusivas estruturais (wcl-tab)
        # O Flashscore usa botões de alternância estilizados com textos específicos
        print("[PASSO 2] Validando se o contêiner de estatísticas individuais está visível...")
        
        try:
            # Seleciona via XPath contendo o texto independente se está em caixa alta ou baixa
            sub_aba_jogadores = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(translate(text(), 'JOGADORES', 'jogadores'), 'jogadores')] | //button[contains(translate(text(), 'JOGADORES', 'jogadores'), 'jogadores')] | //*[@data-testid='wcl-tab-player-statistics']")))
            driver.execute_script("arguments[0].click();", sub_aba_jogadores)
            print("   ✅ Botão ou Aba 'Jogadores' acionado com sucesso!")
            time.sleep(2.0)
        except Exception as e_aba:
            print(f"   ⚠️ Forçando clique alternativo via seletor de classe dinâmico: {e_aba}")
            # Se falhar o texto puro, tentamos buscar elementos de tab genéricos do layout wcl
            tabs = driver.find_elements(By.CSS_SELECTOR, "[class*='tab'], [class*='Tab'], button")
            for t in tabs:
                texto_t = t.text.strip().upper()
                if "JOGADOR" in texto_t or "PLAYER" in texto_t:
                    driver.execute_script("arguments[0].click();", t)
                    print(f"   ✅ Aba acionada via varredura de botões ('{texto_t}')")
                    time.sleep(2.0)
                    break

        # --- PROCESSAMENTO DO FILTRO ATIVO ---
        print("\n[PASSO 3] Buscando os seletores de dados reais (Chutes)...")
        
        # Forçamos a rolagem para ativar o Lazy Loading do Flashscore de tabelas internas
        driver.execute_script("window.scrollTo(0, 350);")
        time.sleep(2.0)
        
        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class^='wcl-tableHeadCell_'], .wcl-tableHeadCell_")
        print(f"📊 Cabeçalhos detectados: {len(cabecalhos_fin)}")
        
        indice_chutes = 5
        for idx, th in enumerate(cabecalhos_fin):
            texto = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
            if any(x in texto for x in ["ALVO", "TARGET", "NO GOL", "CHUTES", "FIN"]):
                indice_chutes = idx
                print(f"   👉 Coluna detectada no índice {indice_chutes} | Texto: '{texto}'")
                break
                
        # Captura agressiva incluindo tabelas e TRs puras geradas pela renderização
        linhas_fin = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, [class^='wcl-table__row_'], [data-testid='wcl-tableRow'], .wcl-table__row_")
        print(f"📊 Total de linhas identificadas: {len(linhas_fin)}")
        
        if len(linhas_fin) == 0:
            # Se mesmo assim der 0, pegamos o HTML interno do container principal pra decifrar a nova tag
            print("🚨 ERRO: Continuou trazendo 0 linhas.")
            container_estat = driver.find_elements(By.CSS_SELECTOR, "[id*='statistics'], [class*='statistics'], [data-testid*='table']")
            if container_estat:
                print(f"🔍 [DEBUG] HTML do container estrutural:\n{container_estat[0].get_attribute('innerHTML')[:500]}")
            else:
                print(f"🔍 [DEBUG] Estrutura do body atual:\n{driver.page_source[:500]}")
        else:
            print("\n📋 Capturas efetuadas com sucesso:")
            for linha in linhas_fin[:5]:
                try:
                    nome_el = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_'], .fp-playerName_")
                    nome = driver.execute_script("return arguments[0].textContent;", nome_el).strip()
                    celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], [class^='wcl-tableBodyCell_']")
                    valor = driver.execute_script("return arguments[0].textContent;", celulas[indice_chutes]).strip() if len(celulas) > indice_chutes else "0"
                    print(f"   👤 {nome} -> {valor}")
                except: pass

    except Exception as e:
        print(f"\n❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE")

if __name__ == "__main__":
    rodar_teste_isolado()
            
