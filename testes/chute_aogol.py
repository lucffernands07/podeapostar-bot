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
    
    # URL do confronto base (H2H)
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/croacia-K8aznggo/inglaterra-j9N9ZNFA/h2h/total/"
    id_jogo_principal = "K8aznggo"
    
    print("\n" + "="*60)
    print("🚀 INICIANDO PROCESSAMENTO APENAS DO ÚLTIMO JOGO DE FORMA ESTRUTURADA")
    print("="*60 + "\n")
    
    try:
        # LOG 1: URL do confronto base (H2H)
        print(f"1. URL DO CONFRONTO (H2H):\n👉 {url_inicial}\n")
        
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Seleciona estritamente a primeira linha da Tabela 1
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
        if not linhas_confrontos:
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
        if not linhas_confrontos:
            print("❌ Nenhuma partida encontrada no H2H.")
            return
            
        primeiro_elemento = linhas_confrontos[0]
        
        try:
            partes_texto = primeiro_elemento.text.split('\n')
            confronto_nome = f"{partes_texto[2].strip()} x {partes_texto[3].strip()}"
        except Exception:
            confronto_nome = "Último Jogo"

        print(f"🔄 Redirecionando para o último confronto: {confronto_nome}...")
        
        url_anterior = driver.current_url
        driver.execute_script("arguments[0].click();", primeiro_elemento)
        
        try:
            WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
        except:
            pass
            
        time.sleep(3)
        
        # LOG 2: URL do último jogo capturada dinamicamente (com slug completo)
        url_jogo_completa = driver.current_url.split("?")[0].strip("/")
        print(f"2. URL DO ÚLTIMO JOGO:\n👉 {url_jogo_completa}\n")
        
        # Captura o ID real apenas para controle interno e segurança
        bloco_url = url_jogo_completa.split("/")[-1]
        match = re.search(r'-([a-zA-Z0-9]{8})$', bloco_url)
        
        if not match:
            print("❌ Não foi possível extrair o ID da URL da partida.")
            return
            
        id_real = match.group(1)
        if id_real == id_jogo_principal:
            print("⚠️ URL não trocou a tempo. O ID capturado pertence ao jogo principal.")
            return

        # --- ABA 1: FINALIZAÇÕES ---
        # Monta a URL baseado no padrão correto: url_do_jogo/resumo/estatisticas-jogadores/finalizacoes/
        url_chutes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
        
        # LOG 3: URL da aba finalizações
        print(f"3. URL DA ABA FINALIZAÇÕES:\n👉 {url_chutes}\n")
        
        driver.get(url_chutes)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
            time.sleep(3)
            
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
            indice_chutes_no_gol = 4
            for idx, th in enumerate(cabecalhos):
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "SHOTS_ON_TARGET" or "ALVO" in texto_th or "GOL" in texto_th:
                    indice_chutes_no_gol = idx
                    break
            
            # LOG 4: Valores de cada jogador da coluna chute no alvo
            print("4. VALORES DE CADA JOGADOR DA COLUNA CHUTE NO ALVO:")
            print("-" * 55)
            
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            for linha in linhas_dados:
                try:
                    nome_jogador = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN").text.strip()
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    
                    celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    if len(celulas_valores) > indice_chutes_no_gol:
                        valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                        chutes_no_alvo = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                        print(f"  👤 {nome_jogador.ljust(25)} ➔ {chutes_no_alvo} chutes no alvo")
                except Exception:
                    continue
            print("-" * 55 + "\n")
        except Exception:
            print("⚠️ Sem dados de Finalizações disponíveis (Aba ausente nesta partida).\n")

        # --- ABA 2: ATAQUE ---
        # Monta a URL baseado no padrão correto: url_do_jogo/resumo/estatisticas-jogadores/ataque/
        url_faltas = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
        
        # LOG 5: URL da aba ataque
        print(f"5. URL DA ABA ATAQUE:\n👉 {url_faltas}\n")
        
        driver.get(url_faltas)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
            time.sleep(3)
            
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
            indice_faltas_sofridas = 4
            for idx, th in enumerate(cabecalhos):
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "FOULS_SUFFERED" or "FALTAS" in texto_th or "SOFRIDAS" in texto_th:
                    indice_faltas_sofridas = idx
                    break
            
            # LOG 6: Valores de cada jogador da coluna falta sofrida
            print("6. VALORES DE CADA JOGADOR DA COLUNA FALTA SOFRIDA:")
            print("-" * 55)
            
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            for linha in linhas_dados:
                try:
                    nome_jogador = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN").text.strip()
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    
                    celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    if len(celulas_valores) > indice_faltas_sofridas:
                        valor_bruto = celulas_valores[indice_faltas_sofridas].text.strip()
                        faltas_sofridas = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                        print(f"  👤 {nome_jogador.ljust(25)} ➔ {faltas_sofridas} faltas sofridas")
                except Exception:
                    continue
            print("-" * 55 + "\n")
        except Exception:
            print("⚠️ Sem dados de Ataque disponíveis (Aba ausente nesta partida).\n")
            
    except Exception as e:
        print(f"\n❌ Erro crítico na execução: {e}")
    finally:
        driver.quit()
        print("="*60)
        print("🏁 Teste finalizado.")
        print("="*60)

if __name__ == "__main__":
    testar_clique_pelo_nome()
    
