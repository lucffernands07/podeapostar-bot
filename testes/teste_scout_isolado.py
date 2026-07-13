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
    wait = WebDriverWait(driver, 15)
    
    # 🔗 URL do jogo mais recente do histórico (América-MG x Cuiabá)
    url_finalizacoes = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/cuiaba-zVvjqDOo/resumo/estatisticas-jogadores/finalizacoes/?mid=QVKCjMJD"
    
    print("\n🔥 TESTE ISOLADO: EXTRAÇÃO DE FINALIZAÇÕES NO ALVO (JOGO MAIS RECENTE)\n" + "="*70)
    print(f"🔗 Acessando: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0) # Tempo de garantia para carregamento dos elementos dinâmicos
        
        # 1️⃣ Captura os hashes dos escudos do topo do jogo para saber quem é Mandante e Visitante
        hash_casa, hash_fora = "", ""
        try:
            hash_casa = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image, [class*='homeLogo'] img").get_attribute("src").split('/')[-1]
            hash_fora = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image, [class*='awayLogo'] img").get_attribute("src").split('/')[-1]
            print(f"🛡️  Mapeamento de Escudos do Jogo:")
            print(f"    🏠 Hash Mandante (Casa): {hash_casa}")
            print(f"    🚀 Hash Visitante (Fora): {hash_fora}\n")
        except Exception as e_hash:
            print(f"⚠️ Não conseguiu ler os hashes do topo: {e_hash}")

        # 2️⃣ Localiza a coluna exata de "Finalizações no Alvo" dinamicamente
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                print(f"🎯 Coluna identificada: '{txt}' encontrada no Índice [{idx}]")
                break
                
        if indice_alvo == -1:
            print("⚠️ Coluna de finalizações no alvo não foi detectada por texto. Usando padrão Índice [5].")
            indice_alvo = 5

        # 3️⃣ Varre todas as linhas de jogadores na tabela e exibe os valores
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"\n📊 Total de linhas brutas encontradas na tabela: {len(linhas)}")
        print("-" * 70)
        
        contagem_impressos = 0
        for linha in linhas:
            try:
                # Localiza o nome do jogador
                nome_element = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                nome_jogador = nome_element.text.strip()
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                # Identifica o escudo do time na própria linha do jogador
                img_linha = linha.find_element(By.CSS_SELECTOR, "[class*='teamLogo'] img, [class*='wcl-teamLogo'] img, img")
                hash_linha = img_linha.get_attribute("src").split('/')[-1]
                
                # Define se o jogador pertence ao Mandante ou Visitante pelo hash do escudo
                if hash_linha == hash_casa:
                    time_pertencente = "MANDANTE"
                elif hash_linha == hash_fora:
                    time_pertencente = "VISITANTE"
                else:
                    time_pertencente = f"DESCONHECIDO (Hash: {hash_linha})"
                
                # Captura todas as células da linha para pegar o valor da coluna correta
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                
                if len(celulas) > indice_alvo:
                    valor_chute_alvo = celulas[indice_alvo].text.strip()
                    print(f"👤 Jogador: {nome_jogador.ljust(22)} | 👥 Time: {time_pertencente.ljust(11)} | 🎯 Chutes no Alvo: {valor_chute_alvo}")
                    contagem_impressos += 1
            except:
                continue

        print("-" * 70)
        print(f"✅ Extração finalizada. Total de jogadores válidos printados: {contagem_impressos}")

    except Exception as e:
        print(f"\n❌ Erro crítico durante a execução do teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_finalizacoes()
    
