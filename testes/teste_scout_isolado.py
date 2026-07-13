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
    
    # URL do jogo histórico aberto a partir do H2H
    url_finalizacoes = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/cuiaba-zVvjqDOo/resumo/estatisticas-jogadores/finalizacoes/?mid=QVKCjMJD"
    
    print("\n🔥 TESTE ISOLADO V7: MAPEAMENTO DE PNG IDENTIFICADO NO H2H\n" + "="*70)
    print(f"🔗 Acessando estatísticas do jogo: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0) # Tempo de garantia para renderização dos elementos
        
        # 🗺️ DICIONÁRIO DE REFERÊNCIA (Coletado na listagem do H2H antes de entrar no jogo)
        # O robô captura o link da imagem e o texto do time exatamente como no seu print:
        dicionario_escudos = {
            "Eut0HLfM-nHqWQgSo.png": "AMÉRICA-MG",
            "COoi5ag5-CWl52SGk.png": "CUIABÁ"
        }
        
        print("📦 Dicionário de Escudos Carregado (Mapeado previamente no H2H):")
        for png, time_nome in dicionario_escudos.items():
            print(f"    • {png} ➔ {time_nome}")
        print("-" * 70)

        # 1️⃣ Localiza a coluna de "Finalizações no Alvo" dinamicamente pelo cabeçalho da tabela
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                print(f"🎯 Coluna 'Chutes no Alvo' identificada no Índice [{idx}]")
                break
                
        # Fallback de segurança caso o cabeçalho mude dinamicamente
        if indice_alvo == -1: 
            indice_alvo = 5
            print(f"⚠️ Cabeçalho não identificado. Usando índice padrão: [{indice_alvo}]")

        # 2️⃣ Captura todas as linhas de jogadores presentes na tabela de scouts
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"\n📊 Total de linhas brutas na tabela: {len(linhas)}")
        print("-" * 70)
        
        contagem_impressos = 0
        
        for linha in linhas:
            try:
                # Extrai o elemento do nome do jogador
                nome_element = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                nome_jogador = nome_element.text.split('\n')[0].strip()
                
                # Desconsidera linhas vazias ou o cabeçalho "TODOS"
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                # Captura especificamente a tag img do escudo do clube para a linha atual
                img_linha = linha.find_element(By.CSS_SELECTOR, "div[class*='teamLogo'] img, [class*='wcl-teamLogo'] img, div[class*='assetContainer'] img")
                src_linha = img_linha.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                # Faz a consulta direta ao seu dicionário mapeado no H2H
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                # Extrai os valores numéricos das colunas correspondentes
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                
                if len(celulas) > indice_alvo:
                    valor_chute_alvo = celulas[indice_alvo].text.strip()
                    print(f"👤 Jogador: {nome_jogador.ljust(22)} | 👥 Time: {time_real.ljust(12)} | 🎯 Chutes no Alvo: {valor_chute_alvo}")
                    contagem_impressos += 1
            except:
                # Ignora linhas de divisão interna ou elementos que não contêm dados de atletas
                continue

        print("-" * 70)
        print(f"✅ Extração finalizada com sucesso. Total de atletas válidos listados: {contagem_impressos}")

    except Exception as e:
        print(f"\n❌ Erro crítico na execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_finalizacoes()
    
