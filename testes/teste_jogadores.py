import os
import sys
import time

# 🔥 PRIMEIRO: Garante que o Python encontre os módulos da pasta raiz no GitHub Actions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora as importações normais do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de análise real do seu arquivo mercados/jogadores.py
from mercados.jogadores import verificar_destaques_jogadores

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
    
    # 🎯 COLOQUE A LIGA E A URL DO CONFRONTO QUE DESEJA TESTAR AQUI:
    nome_liga_teste = "Mundo - Copa do Mundo"
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/escocia-fZRU25WH/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print(f"🚀 INICIANDO ANÁLISE SIMULADA PARA LIGA: {nome_liga_teste}")
    print(f"👉 URL BASE: {url_inicial}")
    print("="*60 + "\n")
    
    historico_chutes = {}
    historico_faltas = {}
    quantidade_jogos = 3
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Seleciona as linhas de confrontos da primeira tabela do H2H
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row") or driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
        if len(linhas_confrontos) < quantidade_jogos:
            print("❌ Partidas insuficientes no H2H para processar os 3 últimos jogos.")
            return

        # --- LOOP PARA PROCESSAR OS 3 JOGOS ---
        for jogo_index in range(quantidade_jogos):
            # Recarrega a página inicial H2H de forma segura a cada rodada
            if jogo_index > 0:
                driver.get(url_inicial)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row") or driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            elemento_alvo = linhas_confrontos[jogo_index]
            url_anterior = driver.current_url
            driver.execute_script("arguments[0].click();", elemento_alvo)
            
            try:
                WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
            except: pass
                
            time.sleep(2.5)
            url_jogo_completa = driver.current_url.split("?")[0].strip("/")
            print(f"🔄 Coletando sub-jogo {jogo_index + 1}: {url_jogo_completa}")

            # --- RASPAGEM DA ABA 1: FINALIZAÇÕES ---
            url_chutes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
            driver.get(url_chutes)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                indice_chutes_no_gol = -1
                
                for idx, th in enumerate(cabecalhos):
                    texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                    alias = str(th.get_attribute("data-analytics-alias")).upper()
                    if "ALVO" in texto_th or alias == "SHOTS_ON_TARGET":
                        indice_chutes_no_gol = idx
                        break
                
                if indice_chutes_no_gol != -1:
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_") or driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                    for linha in linhas_dados:
                        try:
                            nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                            if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper(): continue
                            
                            celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                            if len(celulas_valores) > indice_chutes_no_gol:
                                valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes_no_gol]).strip()
                                chutes_no_alvo = 0 if valor_bruto in ["-", ""] else int(valor_bruto)
                                
                                if nome_jogador not in historico_chutes: historico_chutes[nome_jogador] = []
                                while len(historico_chutes[nome_jogador]) < jogo_index: historico_chutes[nome_jogador].append(0)
                                historico_chutes[nome_jogador].append(chutes_no_alvo)
                        except: continue
            except: pass

            # --- RASPAGEM DA ABA 2: ATAQUE ---
            url_faltas = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
            driver.get(url_faltas)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .fp-playerName_E6lgN")))
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                indice_base = -1
                
                for idx, th in enumerate(cabecalhos):
                    texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                    alias = str(th.get_attribute("data-analytics-alias")).upper()
                    if alias == "FOULS_SUFFERED" or "SOFRIDAS" in texto_th:
                        indice_base = idx
                        break
                
                if indice_base != -1:
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_") or driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                    for linha in linhas_dados:
                        try:
                            nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                            if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper(): continue
                            
                            celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                            if len(celulas_valores) > indice_base:
                                valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_base]).strip()
                                faltas_sofridas = 0 if valor_bruto in ["-", ""] or "%" in valor_bruto or "/" in valor_bruto else int(valor_bruto)
                                
                                if nome_jogador not in historico_faltas: historico_faltas[nome_jogador] = []
                                while len(historico_faltas[nome_jogador]) < jogo_index: historico_faltas[nome_jogador].append(0)
                                historico_faltas[nome_jogador].append(faltas_sofridas)
                        except: continue
            except: pass

        # ========================================================
        # 🔥 PROCESSAMENTO VIA MOTOR MATEMÁTICO REAL (JOGADORES.PY)
        # ========================================================
        print("\n" + "="*60)
        print("⚙️  PROCESSANDO DADOS COLETADOS NO MERCADOS/JOGADORES.PY...")
        print("="*60)
        
        mercados_aprovados = verificar_destaques_jogadores(
            historico_chutes=historico_chutes,
            historico_faltas=historico_faltas,
            quantidade_jogos=quantidade_jogos,
            nome_liga=nome_liga_teste
        )

        if mercados_aprovados:
            print("\n🟢 [APROVADO] O motor do jogadores.py gerou os seguintes mercados:")
            for mercado in mercados_aprovados:
                print(f"  🔶 {mercado['texto']} | Chave: {mercado['chave']}")
        else:
            print("\n🔴 [NEGADO/VAZIO] O motor retornou uma lista vazia. Motivos possíveis: Trava de Liga ou os atletas não atingiram os critérios mínimos de frequência.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de teste: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60)
        print("🏁 Teste de integração finalizado.")
        print("="*60)

if __name__ == "__main__":
    testar_clique_pelo_nome()
