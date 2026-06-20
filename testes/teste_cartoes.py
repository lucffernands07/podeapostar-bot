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

def testar_cartoes_pela_logica_main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    # URL do confronto base (H2H)
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/escocia-fZRU25WH/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 INICIANDO ANÁLISE DOS 3 ÚLTIMOS JOGOS (MERCADO DE CARTÕES - DINÂMICO)")
    print("="*60 + "\n")
    
    # Dicionários para acumular o histórico de cada jogo -> { Nome: [jogo1, jogo2, jogo3] }
    historico_amarelos = {}
    historico_vermelhos = {}
    
    try:
        # LOG 1: URL do confronto base (H2H)
        print(f"1. URL DO CONFRONTO (H2H):\n👉 {url_inicial}\n")
        
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Seleciona as linhas de confrontos da primeira tabela do H2H (Últimos jogos do Mandante)
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
        if not linhas_confrontos:
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
        if len(linhas_confrontos) < 3:
            print("❌ Partidas insuficientes no H2H para processar os 3 últimos jogos.")
            return

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

            # --- RASPAGEM DA ABA: GERAIS ---
            url_gerais = f"{url_jogo_completa}/resumo/estatisticas-jogadores/gerais/"
            driver.get(url_gerais)
            try:
                # Aguarda as novas linhas estruturais de jogadores
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                time.sleep(3)
                
                # Mapeamento dinâmico de colunas idêntico ao de chutes/faltas
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                indice_amarelos = -1
                indice_vermelhos = -1
                
                for idx, th in enumerate(cabecalhos):
                    texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                    alias = str(th.get_attribute("data-analytics-alias")).upper()
                    
                    # Identifica coluna de cartões amarelos
                    if "AMARELO" in texto_th or alias == "YELLOW_CARDS" or texto_th == "CA":
                        indice_amarelos = idx
                    # Identifica coluna de cartões vermelhos
                    if "VERMELHO" in texto_th or alias == "RED_CARDS" or texto_th == "CV":
                        indice_vermelhos = idx

                # Fallback caso não encontre pelo texto (geralmente são as colunas 5 e 6 ou penúltimas antes dos minutos)
                if indice_amarelos == -1:
                    print("  ⚠️ Cabeçalho de amarelos não identificado por texto. Usando mapeamento reverso padrão.")
                
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                if len(linhas_dados) <= 1:
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                    
                for linha in linhas_dados:
                    try:
                        # Extrai o nome do jogador
                        nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                        if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                            continue
                        
                        celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                        
                        # Se achou os índices dinamicamente, usa eles. Se não, usa de trás para frente adaptado (-3 e -2, assumindo que -1 são minutos)
                        idx_am = indice_amarelos if indice_amarelos != -1 else (len(celulas_valores) - 3)
                        idx_vm = indice_vermelhos if indice_vermelhos != -1 else (len(celulas_valores) - 2)
                        
                        if len(celulas_valores) > max(idx_am, idx_vm) and idx_am >= 0:
                            val_amarelo = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_am]).strip()
                            val_vermelho = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_vm]).strip()
                            
                            amarelos = 0 if val_amarelo in ["-", ""] or not val_amarelo.isdigit() else int(val_amarelo)
                            vermelhos = 0 if val_vermelho in ["-", ""] or not val_vermelho.isdigit() else int(val_vermelho)
                            
                            # Acumula Amarelos
                            if nome_jogador not in historico_amarelos:
                                historico_amarelos[nome_jogador] = []
                            while len(historico_amarelos[nome_jogador]) < jogo_index:
                                historico_amarelos[nome_jogador].append(0)
                            historico_amarelos[nome_jogador].append(amarelos)
                            
                            # Acumula Vermelhos
                            if nome_jogador not in historico_vermelhos:
                                historico_vermelhos[nome_jogador] = []
                            while len(historico_vermelhos[nome_jogador]) < jogo_index:
                                historico_vermelhos[nome_jogador].append(0)
                            historico_vermelhos[nome_jogador].append(vermelhos)
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️ Sem dados de Cartões Gerais para este jogo: {e}\n")
                
            print(f"✅ Jogo {jogo_index + 1} coletado.\n" + "-"*40)

        # --- PROCESSAMENTO DOS CONSOLIDADOS E MÉDIAS ---
        print("\n" + "="*60)
        print(f"📊 CONSOLIDADO DE MÉDIAS DOS ÚLTIMOS {quantidade_jogos} JOGOS")
        print("="*60)
        
        medias_totais = {}
        
        print(f"\n🟨 HISTÓRICO DETALHADO POR JOGADOR (Soma Amarelos + Vermelhos):")
        print("-" * 55)
        for jogador, lista_amarelos in historico_amarelos.items():
            lista_vermelhos = historico_vermelhos.get(jogador, [])
            
            while len(lista_amarelos) < quantidade_jogos:
                lista_amarelos.append(0)
            while len(lista_vermelhos) < quantidade_jogos:
                lista_vermelhos.append(0)
                
            lista_combinada = [lista_amarelos[x] + lista_vermelhos[x] for x in range(quantidade_jogos)]
            media = sum(lista_combinada) / quantidade_jogos
            medias_totais[jogador] = media
            
            print(f"  👤 {jogador.ljust(25)} ➔ Média: {media:.1f} cartões/jogo {lista_combinada} (Am: {lista_amarelos} | Vm: {lista_vermelhos})")

        # --- EXIBIÇÃO DOS MELHORES ---
        print("\n" + "="*60)
        print("🏆 DESTAQUES EM INDISCIPLINA SELECIONADOS")
        print("="*60)
        
        if medias_totais and max(medias_totais.values()) > 0:
            jogador_mais_faltoso = max(medias_totais, key=medias_totais.get)
            print(f"🔥 MAIOR TENDÊNCIA DE CARTÃO: {jogador_mais_faltoso} (Média de {medias_totais[jogador_mais_faltoso]:.1f} cartões/jogo)")
        else:
            print(f"🔥 MAIOR TENDÊNCIA DE CARTÃO: Nenhum jogador recebeu cartões nestes jogos.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de médias: {e}")
    finally:
        driver.quit()
        print("="*60)
        print("🏁 Teste de cartões finalizado.")
        print("="*60)

if __name__ == "__main__":
    testar_cartoes_pela_logica_main()
