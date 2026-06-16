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
        
        # Estrutura para acumular os chutes {nome: [chutes_j1, chutes_j2, ...]}
        historico_jogadores = {}
        urls_estatisticas = []
        
        # 1. Coleta os IDs e monta as URLs dos 3 jogos buscando os elementos de forma segura a cada loop
        for i in range(3):
            # Sempre busca os elementos atualizados na página para evitar o erro de Stale Element
            elementos_jogos = driver.find_elements(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
            
            # Se por acaso existirem menos de 3 jogos na tela, interrompe o loop sem quebrar
            if i >= len(elementos_jogos):
                break
                
            elemento = elementos_jogos[i]
            
            print(f"🔄 Clicando na partida da Irlanda do Norte ({i+1}/3)...")
            driver.execute_script("arguments[0].click();", elemento)
            time.sleep(5)
            
            url_final = driver.current_url
            print(f"🔗 URL capturada após o clique: {url_final}")
            
            bloco_visitante = url_final.split("?")[0].strip("/").split("/")[-1]
            match = re.search(r'-([a-zA-Z0-9]{8})$', bloco_visitante)
            
            if match:
                id_real = match.group(1)
                url_alvo = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
                urls_estatisticas.append(url_alvo)
                print(f"3. ✅ URL ALVO FORMATADA: {url_alvo}")
            
            # Retorna para o H2H principal e aguarda o carregamento antes da próxima iteração
            driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        # 2. Executa a raspagem para cada uma das URLs encontradas
        for url_estatisticas in urls_estatisticas:
            print("\n🔀 Redirecionando para validar acesso à página alvo...")
            driver.get(url_estatisticas)
            
            print("⏳ Aguardando renderização dinâmica das estatísticas dos jogadores...")
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                print("⚡ Tabela de estatísticas carregada com sucesso!")
                time.sleep(3)
            except Exception:
                print("⚠️ Tempo de espera esgotado. Tentando extrair com o que estiver pronto...")

            print("\n" + "="*60)
            print("📊 INICIANDO CAPTURA DOS JOGADORES E CHUTES NO ALVO")
            print("="*60)
            
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
                indice_chutes_no_gol = 10
                print(f"⚠️ Alias não encontrado. Usando índice padrão: {indice_chutes_no_gol}")
                
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            if len(linhas_dados) <= 1:
                linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                
            print(f"📋 Total de linhas detectadas para processamento: {len(linhas_dados)}\n")
            
            for linha in linhas_dados:
                try:
                    celula_name = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")
                    nome_jogador = celula_name.text.strip()
                    
                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                        continue
                    
                    celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                    
                    if len(celulas_valores) > indice_chutes_no_gol:
                        valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                        chutes_no_alvo = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                        
                        if nome_jogador not in historico_jogadores:
                            historico_jogadores[nome_jogador] = []
                        historico_jogadores[nome_jogador].append(int(chutes_no_alvo))
                        
                        print(f"🏃‍♂️ {nome_jogador:<25} ➔ Chutes no Alvo: {chutes_no_alvo}")
                except Exception:
                    continue

        # --- TRATAMENTO DE MÉDIAS E EMPATES ---
        print("\n" + "="*60)
        print("📊 CÁLCULO FINAL DAS MÉDIAS DOS CONFRONTOS")
        print("="*60)
        
        jogador_maior_media = None
        maior_media_calculada = -1.0
        
        for jogador, chutes_lista in historico_jogadores.items():
            media_atual = sum(chutes_lista) / len(chutes_lista)
            print(f"🏃‍♂️ {jogador:<25} ➔ Média: {media_atual:.2f} (baseado em {len(chutes_lista)} jogos)")
            
            if media_atual > maior_media_calculada:
                maior_media_calculada = media_atual
                jogador_maior_media = jogador

        print("\n" + "="*60)
        if jogador_maior_media:
            print(f"👑 JOGADOR COM MAIOR MÉDIA DE CHUTES NO ALVO: {jogador_maior_media} ({maior_media_calculada:.2f})")
        else:
            print("⚠️ Nenhuma estatística pôde ser consolidada.")
        print("="*60 + "\n")

        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: RASPAGEM EXECUTADA")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_clique_pelo_nome()
                        
