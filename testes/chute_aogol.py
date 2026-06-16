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
        time.sleep(6)  # Tempo essencial para renderização das tabelas paralelas via JS
        
        # --- ETAPA 4: Identificação da Coluna e Raspagem dos Jogadores ---
        print("\n" + "="*60)
        print("📊 INICIANDO MAPEAMENTO E RASPAGEM DA TABELA PARALELA")
        print("="*60)
        
        # Mapeia dinamicamente onde está a coluna "Finalizações no alvo"
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th[data-testid='wcl-tableHeadCell']")
        
        indice_chutes_no_gol = -1
        contador_colunas = 0
        
        for th in cabecalhos:
            alias = th.get_attribute("data-analytics-alias")
            if alias:
                if alias == "SHOTS_ON_TARGET":
                    indice_chutes_no_gol = contador_colunas
                    print(f"🎯 Coluna 'Finalizações no alvo' identificada no índice de dados: {indice_chutes_no_gol}")
                    break
                contador_colunas += 1
        
        # Fallback de segurança: se a busca por alias falhar, usa a 5ª coluna de dados informada (índice 4)
        if indice_chutes_no_gol == -1:
            indice_chutes_no_gol = 4
            print(f"⚠️ Alerta: Alias não encontrado. Utilizando índice de fallback padrão: {indice_chutes_no_gol} (5ª coluna)")
            
        # Captura todas as linhas de jogadores renderizadas na tela
        # O Flashscore costuma usar 'tr' com 'wcl-tableRow' ou blocos de estatísticas de linha
        linhas_jogadores = driver.find_elements(By.CSS_SELECTOR, "tr[data-testid='wcl-tableRow']")
        
        # Fallback de seletor para linhas se forem divs em vez de tr
        if not linhas_jogadores:
            linhas_jogadores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerStats-row'], .ui-table__row")
            
        print(f"📋 Total de linhas de dados encontradas para processamento: {len(linhas_jogadores)}\n")
        
        # Varredura paralela das linhas
        for idx, linha in enumerate(linhas_jogadores):
            try:
                # Localiza a célula do nome (Geralmente a primeira célula ou elemento com classe name)
                # Tentamos buscar o seletor de nome ou a primeira célula fixa (coluna esquerda)
                celula_nome = linha.find_element(By.CSS_SELECTOR, "td:first-child, [class*='ParticipantName'], [class*='name_']")
                nome_jogador = celula_nome.text.strip()
                
                # Ignora linhas vazias ou de cabeçalho intermediário (ex: texto "TODOS" ou nome de times)
                if not nome_jogador or nome_jogador == "TODOS":
                    continue
                
                # Captura as colunas de dados numéricos (coluna direita da linha)
                celulas_valores = linha.find_elements(By.CSS_SELECTOR, "td[data-testid='wcl-tableCell'], [class*='tableCell_'], td")
                
                # Descontando a primeira coluna (que pode ser o nome) para alinhar com o índice de dados mapeado
                # Se o find_elements capturar tudo incluindo o nome, o ajuste do índice é automático
                ajuste_indice = 1 if len(celulas_valores) > contador_colunas else 0
                indice_final = indice_chutes_no_gol + ajuste_indice
                
                if len(celulas_valores) > indice_final:
                    chutes_no_alvo = celulas_valores[indice_final].text.strip()
                    print(f"🏃‍♂️ {nome_jogador:<25} ➔ Chutes no Alvo: {chutes_no_alvo}")
                else:
                    print(f"🏃‍♂️ {nome_jogador:<25} ➔ Dados insuficientes na linha.")
                    
            except Exception as linha_erro:
                # Evita que uma linha com formato de quebra de seção trave o loop inteiro
                continue
                
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
                    
