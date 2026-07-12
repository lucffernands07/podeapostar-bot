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
    wait = WebDriverWait(driver, 10)
    
    # URL principal do jogo (sem o caminho final truncado)
    url_jogo_base = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA"
    
    print("\n🚀 INICIANDO TESTE ISOLADO COM CLIQUE REAL NAS ABAS\n" + "="*60)
    
    try:
        # 1. Abre a página raiz do jogo histórico
        print(f"[PASSO 1] Abrindo jogo base: {url_jogo_base}")
        driver.get(url_jogo_base)
        time.sleep(3.0)
        
        # 2. Clicar na aba de Estatísticas Principal do Jogo (se não estiver nela)
        try:
            aba_estatisticas = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='estatisticas'], [data-testid='wcl-tab-statistics']")))
            driver.execute_script("arguments[0].click();", aba_estatisticas)
            print("✅ Clicou na aba geral de Estatísticas.")
            time.sleep(2.0)
        except Exception as e:
            print(f"⚠️ Não achou botão de estatísticas ou já estava nela: {e}")

        # 3. Procurar e clicar no botão "JOGADORES" dentro da seção de estatísticas
        try:
            # O Flashscore costuma ter sub-abas: "Equipe" e "Jogadores"
            sub_aba_jogadores = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Jogadores') or contains(text(), 'JOGADORES')]")))
            driver.execute_script("arguments[0].click();", sub_aba_jogadores)
            print("✅ Clicou na sub-aba 'JOGADORES'.")
            time.sleep(2.0)
        except Exception as e:
            print(f"🚨 ERRO ao tentar entrar na sub-aba Jogadores: {e}")

        # 4. Agora sim, clicamos em FINALIZAÇÕES
        try:
            btn_finalizacoes = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Finalizações') or contains(text(), 'Chutes')]")))
            driver.execute_script("arguments[0].click();", btn_finalizacoes)
            print("✅ Filtro 'Finalizações' ativado.")
            time.sleep(2.0)
            
            # --- AGORA EXECUTAMOS A RASPAGEM DE CHUTES ---
            cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class^='wcl-tableHeadCell_']")
            print(f"\n📊 [CHUTES] Cabeçalhos encontrados: {len(cabecalhos_fin)}")
            
            indice_chutes = 5
            for idx, th in enumerate(cabecalhos_fin):
                texto = th.text.strip().upper()
                if any(x in texto for x in ["ALVO", "TARGET", "NO GOL", "CHUTES"]):
                    indice_chutes = idx
                    print(f"👉 Coluna achada no índice {indice_chutes} ({texto})")
                    break
                    
            linhas_fin = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, [class^='wcl-table__row_'], [data-testid='wcl-tableRow']")
            print(f"📊 Linhas de chutes detectadas: {len(linhas_fin)}")
            
            if len(linhas_fin) > 0:
                print("📋 Amostra de jogadores (Chutes):")
                for linha in linhas_fin[:3]:
                    try:
                        nome = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']").text.strip()
                        celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                        valor = celulas[indice_chutes].text.strip() if len(celulas) > indice_chutes else "0"
                        print(f"   👤 {nome} -> {valor} chutes")
                    except: pass
        except Exception as e_fin:
            print(f"❌ Falha na sub-aba finalizações: {e_fin}")

        print("\n" + "="*60)

        # 5. Clicamos em ATAQUE (Para pegar Faltas Sofridas)
        try:
            btn_ataque = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ataque')]")))
            driver.execute_script("arguments[0].click();", btn_ataque)
            print("✅ Filtro 'Ataque' ativado.")
            time.sleep(2.0)
            
            # --- AGORA EXECUTAMOS A RASPAGEM DE FALTAS ---
            cabecalhos_atq = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class^='wcl-tableHeadCell_']")
            print(f"\n📊 [ATAQUE] Cabeçalhos encontrados: {len(cabecalhos_atq)}")
            
            indice_faltas = 5
            for idx, th in enumerate(cabecalhos_atq):
                texto = th.text.strip().upper()
                if any(x in texto for x in ["SOFRIDAS", "FS", "FOULS SUFFERED"]):
                    indice_faltas = idx
                    print(f"👉 Coluna achada no índice {indice_faltas} ({texto})")
                    break
                    
            linhas_atq = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, [class^='wcl-table__row_'], [data-testid='wcl-tableRow']")
            print(f"📊 Linhas de ataque detectadas: {len(linhas_atq)}")
            
            if len(linhas_atq) > 0:
                print("📋 Amostra de jogadores (Faltas Sofridas):")
                for linha in linhas_atq[:3]:
                    try:
                        nome = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']").text.strip()
                        celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                        valor = celulas[indice_faltas].text.strip() if len(celulas) > indice_faltas else "0"
                        print(f"   👤 {nome} -> {valor} faltas sofridas")
                    except: pass
        except Exception as e_atq:
            print(f"❌ Falha na sub-aba ataque: {e_atq}")

    except Exception as e:
        print(f"\n❌ Erro Geral: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE")

if __name__ == "__main__":
    rodar_teste_isolado()
        
