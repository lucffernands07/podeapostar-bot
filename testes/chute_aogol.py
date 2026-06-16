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
    print("🚀 INICIANDO COLETA DOS 3 ÚLTIMOS JOGOS (H2H)")
    print("="*60 + "\n")
    
    # Estrutura para acumular os dados dos jogadores {nome: [chutes_jogo1, chutes_jogo2, ...]}
    historico_jogadores = {}
    
    try:
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Localiza todas as partidas que contenham 'Irlanda do Norte' na primeira tabela do H2H
        elementos_jogos = driver.find_elements(By.XPATH, "//div[contains(@class, 'h2h__section')][1]//div[contains(@class, 'h2h__row')]//*[contains(text(), 'Irlanda do Norte')]")
        
        # Filtra para pegar no máximo os 3 últimos jogos disponíveis
        elementos_alvo = elementos_jogos[:3]
        total_jogos_encontrados = len(elementos_alvo)
        print(f"📋 Encontrados {total_jogos_encontrados} jogos recentes da Irlanda do Norte para analisar.\n")
        
        urls_para_processar = []
        
        # --- ETAPA 1: MAPEAMENTO E EXTRAÇÃO DAS 3 DE FINALIZAÇÕES ---
        for i, elemento in enumerate(elementos_alvo):
            try:
                print(f"🔄 Identificando link do Jogo {i+1}...")
                driver.execute_script("arguments[0].click();", elemento)
                time.sleep(4)
                
                # Troca para a nova janela se ela abrir em aba, ou usa a atual
                abas = driver.window_handles
                if len(abas) > 1:
                    driver.switch_to.window(abas[-1])
                
                url_final = driver.current_url
                
                # Trata o ID do visitante
                bloco_visitante = url_final.split("?")[0].strip("/").split("/")[-1]
                match = re.search(r'-([a-zA-Z0-9]{8})$', bloco_visitante)
                
                if match:
                    id_real = match.group(1)
                    # Mantém o padrão exato da URL que você validou
                    url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
                    urls_para_processar.append(url_estatisticas)
                    print(f"🔗 URL {i+1} Gerada: {url_estatisticas}")
                
                # Se abriu nova aba, fecha e volta para a principal do H2H
                if len(abas) > 1:
                    driver.close()
                    driver.switch_to.window(abas[0])
                else:
                    # Se navegou na mesma aba, retorna ao H2H original para o próximo clique
                    driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    # Re-mapeia os elementos para não dar StaleElementReferenceException
                    elementos_jogos = driver.find_elements(By.XPATH, "//div[contains(@class, 'h2h__section')][1]//div[contains(@class, 'h2h__row')]//*[contains(text(), 'Irlanda do Norte')]")
                    elementos_alvo = elementos_jogos[:3]
                    
            except Exception as e_jogo:
                print(f"⚠️ Erro ao capturar URL do jogo {i+1}: {e_jogo}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue

        # --- ETAPA 2: PROCESSAMENTO DOS JOGOS E ACÚMULO DE CHUTES ---
        for idx_url, url_alvo in enumerate(urls_para_processar):
            print("\n" + "-"*60)
            print(f"📊 RASPANDO DADOS: JOGO {idx_url + 1}/{len(urls_para_processar)}")
            print("-"*60)
            
            driver.get(url_alvo)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                time.sleep(3)
            except Exception:
                print(f"⚠️ Tempo limite esgotado para o jogo {idx_url + 1}. Pulando...")
                continue
                
            # Mapeamento do índice dinâmico (SHOTS_ON_TARGET)
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY")
            indice_chutes_no_gol = -1
            contador_colunas = 0
            
            for th in cabecalhos:
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "SHOTS_ON_TARGET" or "FINALIZAÇÕES NO ALVO" in texto_th:
                    indice_chutes_no_gol = contador_colunas
                    break
                contador_colunas += 1
                
            if indice_chutes_no_gol == -1:
                indice_chutes_no_gol = 10
                
            # Varredura das Linhas da Partida Atual
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            for linha in linhas_dados:
                try:
                    celula_name = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")
                    nome_jogador = celula_name.text.strip()
                    
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                        
                    celulas_valores = line.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_") if 'line' in locals() else linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    
                    if len(celulas_valores) > indice_chutes_no_gol:
                        valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                        chutes = 0 if valor_bruto == "-" or valor_bruto == "" else int(valor_bruto)
                        
                        # Adiciona o valor mapeado na lista histórica do atleta
                        if nome_jogador not in historico_jogadores:
                            historico_jogadores[nome_jogador] = []
                        historico_jogadores[nome_jogador].append(chutes)
                except Exception:
                    continue

        # --- ETAPA 3: CÁLCULO DAS MÉDIAS E EXIBIÇÃO DO VENCEDOR ---
        print("\n" + "="*60)
        print("📈 RESULTADO CONSOLIDADO: MÉDIAS DOS ÚLTIMOS 3 JOGOS")
        print("="*60)
        
        jogador_top = None
        maior_media = -1.0
        
        for jogador, lista_chutes in historico_jogadores.items():
            # Calcula a média baseada no número de partidas que o jogador participou (dentro das 3 analisadas)
            media = sum(lista_chutes) / len(lista_chutes)
            print(f"🏃‍♂️ {jogador:<25} ➔ Jogos analisados: {len(lista_chutes)} | Total Chutes: {sum(lista_chutes)} | Média: {media:.2f}")
            
            # Se for estritamente maior, atualiza o líder (mantém o primeiro inserido se houver empate de médias)
            if media > maior_media:
                maior_media = media
                jogador_top = jogador

        print("\n" + "="*60)
        if jogador_top:
            print(f"👑 JOGADOR COM MAIOR MÉDIA: {jogador_top} (Média: {maior_media:.2f})")
        else:
            print("⚠️ Nenhum jogador com estatísticas registradas foi computado.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste expandido: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_clique_pelo_nome()
                    
