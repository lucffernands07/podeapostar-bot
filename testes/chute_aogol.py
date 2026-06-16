import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
        # --- ETAPA 1 e 2: Navegação e Descoberta de ID ---
        driver.get("https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        elemento_jogo = driver.find_element(By.XPATH, "//*[contains(text(), 'Irlanda do Norte')]")
        
        print("🔄 Clicando na partida da Irlanda do Norte...")
        driver.execute_script("arguments[0].click();", elemento_jogo)
        
        time.sleep(5)
        
        url_final = driver.current_url
        print(f"🔗 URL capturada após o clique: {url_final}")
        
        url_limpa = url_final.split("?")[0]
        partes_url = url_limpa.strip("/").split("/")
        ultimo_bloco = partes_url[-1] 
        id_real = ultimo_bloco.split("-")[-1]
        
        url_estatisticas = f"https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/irlanda-do-norte-{id_real}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"\n3. ✅ URL ALVO FORMATADA: {url_estatisticas}")
        
        # --- ETAPA 3: Acesso à Página de Estatísticas ---
        print("\n🔀 Redirecionando para a página alvo de finalizações...")
        driver.get(url_estatisticas)
        time.sleep(6)
        
        # --- ETAPA 4: Identificação da Coluna e Raspagem Mapeada ---
        print("\n" + "="*60)
        print("📊 INICIANDO MAPEAMENTO E RASPAGEM DA TABELA PARALELA")
        print("="*60)
        
        # 1. Mapeia o índice da coluna usando o testid correto do cabeçalho
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell']")
        
        indice_chutes_no_gol = -1
        contador_colunas = 0
        
        for th in cabecalhos:
            alias = th.get_attribute("data-analytics-alias")
            if alias:
                if alias == "SHOTS_ON_TARGET":
                    indice_chutes_no_gol = contador_colunas
                    print(f"🎯 Coluna 'Finalizações no alvo' identificada no índice: {indice_chutes_no_gol}")
                    break
                contador_colunas += 1
        
        if indice_chutes_no_gol == -1:
            indice_chutes_no_gol = 4
            print(f"⚠️ Alerta: Alias não encontrado. Usando índice padrão: {indice_chutes_no_gol}")

        # 2. Captura todas as células de NOMES dos jogadores (Tabela Esquerda Fira)
        # O Flashscore costuma usar classes com 'participant' ou 'name' para os atletas
        celulas_nomes = driver.find_elements(By.CSS_SELECTOR, "[class*='participantName'], [class*='name_'], td:first-child")
        
        # Filtragem para remover textos indesejados da captura de nomes
        nomes_filtrados = []
        for celula in celulas_nomes:
            txt = celula.text.strip()
            if txt and txt != "TODOS" and "Rating" not in txt and txt != "JOGADOR":
                nomes_filtrados.append(txt)

        # 3. Captura todas as LINHAS de dados numéricos (Tabela Direita Móvel)
        # Usamos uma busca por elementos de linha genéricos ou de tabela
        linhas_dados = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow'], tr")
        
        print(f"📋 Jogadores filtrados: {len(nomes_filtrados)} | Linhas de dados bruto: {len(linhas_dados)}")
        
        # Varremos os nomes e associamos com as colunas numéricas de cada linha correspondente
        contador_sucesso = 0
        for idx, nome in enumerate(nomes_filtrados):
            try:
                if idx >= len(linhas_dados):
                    break
                    
                linha_atual = lines_dados[idx] if 'linhas_dados' in locals() else linhas_dados[idx]
                
                # Busca as células de valores numéricos baseando-se no HTML que você forneceu
                celulas_valores = linha_atual.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
                
                if len(celulas_valores) > indice_chutes_no_gol:
                    # Captura o texto interno (que pode ser o "-" ou o número de chutes)
                    valor_bruto = celulas_valores[indice_chutes_no_gol].text.strip()
                    
                    # Tratamento: se for o traço "-", convertemos para "0" como você pediu
                    chutes_no_alvo = "0" if valor_bruto == "-" or valor_bruto == "" else valor_bruto
                    
                    print(f"🏃‍♂️ {nome:<25} ➔ Chutes no Alvo: {chutes_no_alvo}")
                    contador_sucesso += 1
            except Exception as e_linha:
                continue
                
        if contador_sucesso == 0:
            print("\n⚠️ Nenhuma linha processada com sucesso. Tentando modo de varredura direta por linha...")
            # Fallback direto: se a separação falhar, tentamos ler cada linha inteira pelo testid padrão
            linhas_gerais = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
            for lg in linhas_gerais:
                texto_total = lg.text.replace("\n", " ").strip()
                if texto_total and "TODOS" not in texto_total:
                    print(f"📄 Linha Bruta Detectada: {texto_total}")

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
    
