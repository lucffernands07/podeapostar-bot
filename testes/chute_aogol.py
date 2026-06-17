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

# Garante que o Python encontre os módulos da pasta raiz no GitHub Actions
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
    print("🚀 INICIANDO PROCESSAMENTO DOS 3 ÚLTIMOS JOGOS (H2H)")
    print("="*60 + "\n")
    
    try:
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        historico_chutes = {}
        historico_faltas = {}
        urls_chutes = []
        urls_ataque = []
        
        # 1. Mapeia e armazena as URLs das duas abas para os 3 últimos jogos
        for i in range(3):
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
            if not linhas_confrontos:
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            if i >= len(linhas_confrontos):
                break
                
            elemento = linhas_confrontos[i]
            
            try:
                partes_texto = elemento.text.split('\n')
                mandante = partes_texto[2].strip()
                visitante = partes_texto[3].strip()
                confronto_formatado = f"{mandante} x {visitante}"
            except Exception:
                confronto_formatado = f"Jogo {i+1}"

            print(f"🔄 Mapeando partida: {confronto_formatado} ({i+1}/3)...")
            driver.execute_script("arguments[0].click();", elemento)
            time.sleep(5)
            
            url_final = driver.current_url
            bloco_url = url_final.split("?")[0].strip("/").split("/")[-1]
            match = re.search(r'-([a-zA-Z0-9]{8})$', bloco_url)
            
            if match:
                id_real = match.group(1)
                # Guarda a URL de Chutes no Alvo (Finalizações)
                urls_chutes.append(f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/")
                # Guarda a URL de Faltas Sofridas (Ataque)
                urls_ataque.append(f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/ataque/")
            
            driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        # ==========================================
        # 2. RASPAGEM: CATEGORIA CHUTES NO ALVO
        # ==========================================
        for url in urls_chutes:
            driver.get(url)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                time.sleep(3)
            except Exception:
                continue
            
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY")
            indice_coluna = -1
            contador = 0
            for th in cabecalhos:
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "SHOTS_ON_TARGET" or "FINALIZAÇÕES NO ALVO" in texto_th:
                    indice_coluna = contador
                    break
                contador += 1
            if indice_coluna == -1:
                indice_coluna = 10
                
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            for linha in linhas_dados:
                try:
                    nome_jogador = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN").text.strip()
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    if len(celulas) > indice_coluna:
                        val = celulas[indice_coluna].text.strip()
                        qtd = "0" if val == "-" or val == "" else val
                        if nome_jogador not in historico_chutes:
                            historico_chutes[nome_jogador] = []
                        historico_chutes[nome_jogador].append(int(qtd))
                except Exception:
                    continue

        # --- LOG DOS CHUTES NO ALVO ---
        jogador_top_chutes = None
        media_top_chutes = -1.0
        for jogador, lista in historico_chutes.items():
            media = sum(lista) / len(lista)
            if media > media_top_chutes:
                media_top_chutes = media
                jogador_top_chutes = jogador

        print("\n" + "="*60)
        if jogador_top_chutes:
            print(f"👑 JOGADOR COM MAIOR MÉDIA DE CHUTES NO ALVO: {jogador_top_chutes} ({media_top_chutes:.2f})")
        else:
            print("⚠️ Nenhuma estatística de Chutes no Alvo pôde ser consolidada.")
        print("="*60 + "\n")


        # ==========================================
        # 3. RASPAGEM: CATEGORIA FALTAS SOFRIDAS
        # ==========================================
        for url in urls_ataque:
            driver.get(url)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                time.sleep(3)
            except Exception:
                continue
            
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY")
            indice_coluna = -1
            contador = 0
            for th in cabecalhos:
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "FOULS_SUFFERED" or "FALTAS SOFRIDAS" in texto_th or "FALTAS" in texto_th:
                    indice_coluna = contador
                    break
                contador += 1
            if indice_coluna == -1:
                indice_coluna = 4
                
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            for linha in linhas_dados:
                try:
                    nome_jogador = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN").text.strip()
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    if len(celulas) > indice_coluna:
                        val = celulas[indice_coluna].text.strip()
                        qtd = "0" if val == "-" or val == "" else val
                        if nome_jogador not in historico_faltas:
                            historico_faltas[nome_jogador] = []
                        historico_faltas[nome_jogador].append(int(qtd))
                except Exception:
                    continue

        # --- LOG DAS FALTAS SOFRIDAS ---
        jogador_top_faltas = None
        media_top_faltas = -1.0
        for jogador, lista in historico_faltas.items():
            media = sum(lista) / len(lista)
            if media > media_top_faltas:
                media_top_faltas = media
                jogador_top_faltas = jogador

        print("="*60)
        if jogador_top_faltas:
            print(f"👑 JOGADOR COM MAIOR MÉDIA DE FALTAS SOFRIDAS: {jogador_top_faltas} ({media_top_faltas:.2f})")
        else:
            print("⚠️ Nenhuma estatística de Faltas Sofridas pôde ser consolidada.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_clique_pelo_nome()
        
