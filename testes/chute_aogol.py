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
    print("🚀 INICIANDO CLIQUE DIRETO NO TEXTO DO JOGO")
    print("="*60 + "\n")
    
    try:
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        
        # Espera as linhas do H2H carregarem na tela
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Procura o elemento exato que contém o texto da partida anterior
        elemento_jogo = driver.find_element(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
        
        print("🔄 Clicando na partida da Irlanda do Norte...")
        driver.execute_script("arguments[0].click();", elemento_jogo)
        
        # Aguarda a navegação e mudança de página completarem
        time.sleep(5)
        
        # Captura a URL final resultante do clique
        url_final = driver.current_url
        print(f"🔗 URL capturada após o clique: {url_final}")
        
        # --- AJUSTE CIRÚRGICO DA REGEX PARA PEGAR O ID DA IRLANDA DO NORTE ---
        # Filtra para buscar o padrão de 8 caracteres apenas no último bloco da URL do jogo
        bloco_visitante = url_final.split("?")[0].strip("/").split("/")[-1]
        match = re.search(r'-([a-zA-Z0-9]{8})$', bloco_visitante)
        
        if match:
            id_real = match.group(1)
            url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
            print(f"\n3. ✅ URL ALVO FORMATADA: {url_estatisticas}")
            
            print("\n🔀 Redirecionando para validar acesso à página alvo...")
            driver.get(url_estatisticas)
            
            # --- CONTINUAÇÃO AQUI: ESPERA ATÉ A TABELA CARREGAR DE VERDADE ---
            print("⏳ Aguardando renderização dinâmica das estatísticas dos jogadores...")
            try:
                # Modificado para focar no elemento de célula de jogador que você extraiu no HTML
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                print("⚡ Tabela de estatísticas carregada com sucesso!")
                time.sleep(3)  # Respiro para o JS preencher os nós de texto
            except Exception:
                print("⚠️ Tempo de espera esgotado. Tentando extrair com o que estiver pronto...")

            print("\n" + "="*60)
            print("📊 INICIANDO CAPTURA DOS JOGADORES E CHUTES NO ALVO")
            print("="*60)
            
            # 1. Mapeamento dinâmico da coluna desejada
            cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY")
            indice_chutes_no_gol = -1
            contador_colunas = 0
            
            for th in cabecalhos:
                texto_th = th.text.strip().upper()
                alias = th.get_attribute("data-analytics-alias")
                if alias == "SHOTS_ON_TARGET" or "FINALIZAÇÕES NO ALVO" in texto_th:
                    indice_chutes_no_gol = contador_colunas
                    print(f"🎯 Coluna 'Finalizações no alvo' identificada no índice: {indice_chutes_no_gol}")
                    break
                contador_colunas += 1
                
            if indice_chutes_no_gol == -1:
                indice_chutes_no_gol = 10  # Mantém o índice 10 pego no seu último log de sucesso como fallback
                print(f"⚠️ Alias não encontrado. Usando índice padrão: {indice_chutes_no_gol}")
                
            # 2. Varredura das Linhas Reais (Mudado para buscar as linhas da tabela tradicional 'tr' ou containers de linha nativos)
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            
            # Se a busca falhar por usar tags estruturais puras, faz o fallback para varredura ampla de elementos de jogador
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            print(f"📋 Total de linhas detectadas para processamento: {len(linhas_dados)}\n")
            
            for linha in linhas_dados:
                try:
                    # Busca o nome usando a classe exata fornecida: .fp-playerName_E6lgN
                    celula_name = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")
                    nome_jogador = celula_name.text.strip()
                    
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    
                    # Coleta os valores usando as tags de texto que você indicou no HTML (wcl-scores-simple-text-01) ou células normais
                    celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    
                    if len(celulas_valores) > indice_chutes_no_gol:
                        valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                        
                        # Converte o traço "-" do Flashscore para "0"
                        chutes_no_alvo = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                        
                        print(f"🏃‍♂️ {nome_jogador:<25} ➔ Chutes no Alvo: {chutes_no_alvo}")
                except Exception:
                    continue

            print("\n" + "="*60)
            print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: RASPAGEM EXECUTADA")
            print("="*60 + "\n")
        else:
            raise Exception(f"Não foi possível encontrar o padrão de ID de 8 dígitos na URL: {url_final}")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_clique_pelo_nome()
                
