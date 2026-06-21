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
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/escocia-fZRU25WH/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 INICIANDO ANÁLISE DOS 3 ÚLTIMOS JOGOS COM MÉDIAS E DESTAQUES")
    print("="*60 + "\n")
    
    # Dicionários para acumular o histórico de cada jogo -> { Nome: [jogo1, jogo2, jogo3] }
    historico_chutes = {}
    historico_faltas = {}
    
    try:
        # LOG 1: URL do confronto base (H2H)
        print(f"1. URL DO CONFRONTO (H2H):\n👉 {url_inicial}\n")
        
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Seleciona as linhas de confrontos da primeira tabela do H2H
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
        if not linhas_confrontos:
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
        if len(linhas_confrontos) < 3:
            print("❌ Partidas insuficientes no H2H para processar os 3 últimos jogos.")
            return

        # ALTERADO PARA 3 JOGOS
        quantidade_jogos = 3
        urls_jogos_alvo = []

        # Mapeia os confrontos antes de navegar
        for i in range(quantidade_jogos):
            try:
                partes_texto = linhas_confrontos[i].text.split('\n')
                nome_confronto = f"{partes_texto[2].strip()} x {partes_texto[3].strip()}"
            except:
                nome_confronto = f"Jogo {i+1}"
            urls_jogos_alvo.append(nome_confronto)

        # --- LOOP PARA PROCESSAR OS 3 JOGOS ---
        for jogo_index in range(quantidade_jogos):
            print(f"🔄 Redirecionando para o Jogo {jogo_index + 1}: {urls_jogos_alvo[jogo_index]}...")
            
            # Recarrega a página inicial H2H caso o driver venha de outra aba
            if jogo_index > 0:
                driver.get(url_inicial)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row") or driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            elemento_alvo = linhas_confrontos[jogo_index]
            url_anterior = driver.current_url
            driver.execute_script("arguments[0].click();", elemento_alvo)
            
            try:
                WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
            except:
                pass
                
            time.sleep(3)
            url_jogo_completa = driver.current_url.split("?")[0].strip("/")
            print(f"👉 URL DO JOGO {jogo_index + 1}:\n   {url_jogo_completa}\n")

            # --- RASPAGEM DA ABA 1: FINALIZAÇÕES ---
            url_chutes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
            driver.get(url_chutes)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                time.sleep(3)
                
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                indice_chutes_no_gol = 10
                
                for idx, th in enumerate(cabecalhos):
                    texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                    alias = str(th.get_attribute("data-analytics-alias")).upper()
                    if "ALVO" in texto_th or alias == "SHOTS_ON_TARGET":
                        indice_chutes_no_gol = idx
                        break
                
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                if len(linhas_dados) <= 1:
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                    
                for linha in linhas_dados:
                    try:
                        nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                        if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                            continue
                        
                        celulas_valores = inline_cells = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                        if len(celulas_valores) > indice_chutes_no_gol:
                            valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes_no_gol]).strip()
                            chutes_no_alvo = 0 if valor_bruto == "-" or valor_bruto == "" else int(valor_bruto)
                            
                            if nome_jogador not in historico_chutes:
                                historico_chutes[nome_jogador] = []
                            
                            # Garante o alinhamento caso o jogador não tenha dados nos jogos anteriores
                            while len(historico_chutes[nome_jogador]) < jogo_index:
                                historico_chutes[nome_jogador].append(0)
                                
                            historico_chutes[nome_jogador].append(chutes_no_alvo)
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️ Sem dados de Finalizações para este jogo.\n")

            # --- RASPAGEM DA ABA 2: ATAQUE ---
            url_faltas = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
            driver.get(url_faltas)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .fp-playerName_E6lgN")))
                time.sleep(4)
                
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                indice_base = 13
                
                for idx, th in enumerate(cabecalhos):
                    texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                    alias = str(th.get_attribute("data-analytics-alias")).upper()
                    if alias == "FOULS_SUFFERED" or "SOFRIDAS" in texto_th:
                        indice_base = idx
                        break
                
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                if len(linhas_dados) <= 1:
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
                # Algoritmo de Varredura Reversa Dinâmica
                indice_real_faltas = -1
                for test_idx in range(indice_base, -1, -1):
                    encontrou_valor_valido = False
                    for linha in linhas_dados:
                        try:
                            celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                            if len(celulas_valores) > test_idx:
                                val_bruto = driver.execute_script("return arguments[0].textContent;", celulas_valores[test_idx]).strip()
                                if val_bruto.isdigit() and int(val_bruto) >= 1:
                                    encontrou_valor_valido = True
                                    break
                        except:
                            continue
                    if encontrou_valor_valido:
                        indice_real_faltas = test_idx
                        break
                
                if indice_real_faltas == -1:
                    indice_real_faltas = indice_base - 1
                
                for linha in linhas_dados:
                    try:
                        el_nome = None
                        try:
                            el_nome = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")
                        except:
                            el_nome = linha.find_element(By.CSS_SELECTOR, "[class*='playerName']")
                            
                        nome_jogador = driver.execute_script("return arguments[0].textContent;", el_nome).strip()
                        if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                            continue
                        
                        celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                        if len(celulas_valores) > indice_real_faltas:
                            valor_bruto = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_real_faltas]).strip()
                            faltas_sofridas = 0 if valor_bruto == "-" or valor_bruto == "" or "%" in valor_bruto or "/" in valor_bruto else int(valor_bruto)
                            
                            if nome_jogador not in historico_faltas:
                                historico_faltas[nome_jogador] = []
                                
                            # Garante o alinhamento caso o jogador não tenha dados nos jogos anteriores
                            while len(historico_faltas[nome_jogador]) < jogo_index:
                                historico_faltas[nome_jogador].append(0)
                                
                            historico_faltas[nome_jogador].append(faltas_sofridas)
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️ Sem dados de Ataque para este jogo.\n")
                
            print(f"✅ Jogo {jogo_index + 1} coletado.\n" + "-"*40)

        # --- PROCESSAMENTO DOS CONSOLIDADOS E MÉDIAS ---
        print("\n" + "="*60)
        print(f"📊 CONSOLIDADO DE MÉDIAS DOS ÚLTIMOS {quantidade_jogos} JOGOS")
        print("="*60)
        
        medias_chutes = {}
        medias_faltas = {}
        
        print(f"\n📈 MERCADO: CHUTES NO ALVO (Médias baseadas em {quantidade_jogos} jogos):")
        print("-" * 55)
        for jogador, lista_valores in historico_chutes.items():
            while len(lista_valores) < quantidade_jogos:
                lista_valores.append(0)
            media = sum(lista_valores) / quantidade_jogos
            medias_chutes[jogador] = media
            print(f"  👤 {jogador.ljust(25)} ➔ Média: {media:.1f} chutes/jogo {lista_valores}")
            
        print(f"\n📉 MERCADO: FALTAS SOFRIDAS (Médias baseadas em {quantidade_jogos} jogos):")
        print("-" * 55)
        for jogador, lista_valores in historico_faltas.items():
            while len(lista_valores) < quantidade_jogos:
                lista_valores.append(0)
            media = sum(lista_valores) / quantidade_jogos
            medias_faltas[jogador] = media
            print(f"  👤 {jogador.ljust(25)} ➔ Média: {media:.1f} faltas sofridas {lista_valores}")

        # --- EXIBIÇÃO DOS MELHORES DE CADA MERCADO ---
        print("\n" + "="*60)
        print("🏆 MELHORES DE CADA MERCADO (DESTAQUES SELECIONADOS)")
        print("="*60)
        
        if medias_chutes:
            melhor_chutador = max(medias_chutes, key=medias_chutes.get)
            print(f"🔥 MELHOR EM CHUTES NO ALVO: {melhor_chutador} (Média de {medias_chutes[melhor_chutador]:.1f}/jogo)")
        else:
            print(f"🔥 MELHOR EM CHUTES NO ALVO: Nenhum dado capturado.")
            
        if medias_faltas:
            melhor_fustigado = max(medias_faltas, key=medias_faltas.get)
            print(f"🤕 MAIS CAÇADO (FALTAS SOFRIDAS): {melhor_fustigado} (Média de {medias_faltas[melhor_fustigado]:.1f}/jogo)")
        else:
            print(f"🤕 MAIS CAÇADO (FALTAS SOFRIDAS): Nenhum dado capturado.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de médias: {e}")
    finally:
        driver.quit()
        print("="*60)
        print("🏁 Teste de médias e mercados finalizado com sucesso.")
        print("="*60)

if __name__ == "__main__":
    testar_clique_pelo_nome()
                           
