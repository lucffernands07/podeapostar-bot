import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_finalizacoes():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URL do jogo histórico
    url_finalizacoes = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/cuiaba-zVvjqDOo/resumo/estatisticas-jogadores/finalizacoes/?mid=QVKCjMJD"
    
    print("\n🔥 TESTE ISOLADO V8: MAPEAMENTO DE PNG CORRIGIDO DENTRO DA CELULA DO JOGADOR\n" + "="*70)
    print(f"🔗 Acessando estatísticas do jogo: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0)
        
        # 🗺️ DICIONÁRIO DE REFERÊNCIA (Capturado no H2H)
        dicionario_escudos = {
            "Eut0HLfM-nHqWQgSo.png": "AMÉRICA-MG",
            "COoi5ag5-CWl52SGk.png": "CUIABÁ"
        }
        
        print("📦 Dicionário de Escudos Carregado:")
        for png, time_nome in dicionario_escudos.items():
            print(f"    • {png} ➔ {time_nome}")
        print("-" * 70)

        # 1️⃣ Localiza a coluna de "Finalizações no Alvo" dinamicamente pelo cabeçalho
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                print(f"🎯 Coluna 'Chutes no Alvo' identificada no Índice [{idx}]")
                break
                
        if indice_alvo == -1: 
            indice_alvo = 5

        # 2️⃣ Captura as linhas da tabela
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"\n📊 Total de linhas brutas na tabela: {len(linhas)}")
        print("-" * 70)
        
        contagem_impressos = 0
        
        for linha in linhas:
            try:
                # Localiza especificamente a célula do jogador (a primeira coluna td com conteúdo)
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                
                # Extrai o nome do jogador buscando a classe exata do seu print
                nome_element = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']")
                nome_jogador = nome_element.text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                # 🎯 SELETOR CORRIGIDO: Busca a img EXCLUSIVAMENTE dentro da div do logo do time, ignorando a foto do rosto
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-teamLogo_sFhMr img")
                src_linha = img_logo.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                # Faz a consulta ao dicionário mapeado
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                # Extrai os valores das estatísticas
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                
                if len(celulas) > indice_alvo:
                    valor_chute_alvo = celulas[indice_alvo].text.strip()
                    print(f"👤 Jogador: {nome_jogador.ljust(22)} | 👥 Time: {time_real.ljust(12)} | 🎯 Chutes no Alvo: {valor_chute_alvo}")
                    contagem_impressos += 1
            except:
                continue

        print("-" * 70)
        print(f"✅ Extração finalizada. Total de atletas listados: {contagem_impressos}")

    except Exception as e:
        print(f"\n❌ Erro crítico na execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_finalizacoes()
