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
    
    url_finalizacoes = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/cuiaba-zVvjqDOo/resumo/estatisticas-jogadores/finalizacoes/?mid=QVKCjMJD"
    
    print("\n🔥 TESTE ISOLADO V4: IDENTIFICAÇÃO PELO BOTÃO SELETOR DO TIME\n" + "="*70)
    print(f"🔗 Acessando: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0) # Tempo de garantia para carregamento
        
        # Padrões do confronto atual caso falhe a leitura do texto completo do topo
        nome_casa_topo = "AMÉRICA-MG"
        nome_fora_topo = "CUIABÁ"

        # 1️⃣ Mapeia a coluna exata de "Finalizações no Alvo" dinamicamente
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th[data-testid='wcl-tableHeadCell'], th, .wcl-tableHeadCell_")
        indice_alvo = -1
        
        print("📋 Buscando coluna de alvo nos cabeçalhos...")
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                print(f"   🎯 Coluna 'Finalizações no Alvo' detectada no Índice [{idx}]")
                break
                
        if indice_alvo == -1:
            print("⚠️ Coluna não detectada por texto. Usando padrão Índice [5].")
            indice_alvo = 5

        # 2️⃣ Mapeia a ordem dos blocos ou linhas de acordo com o seletor mapeado
        # Procuramos os botões seletores de time presentes na tabela (ex: fp-teamSelector)
        seletores_time = driver.find_elements(By.CSS_SELECTOR, "[class*='fp-teamSelector'], [data-testid='wcl-selectButton']")
        times_mapeados_tabela = []
        
        for sel in seletores_time:
            try:
                img_sel = sel.find_element(By.TAG_NAME, "img")
                alt_text = img_sel.get_attribute("alt") or ""
                if alt_text:
                    times_mapeados_tabela.append(alt_text.strip().upper())
            except:
                pass
                
        print(f"\n🛡️ Times detectados nos seletores da tabela: {times_mapeados_tabela}")

        # 3️⃣ Varre todas as linhas da tabela de jogadores
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"\n📊 Total de linhas de elementos encontradas: {len(linhas)}")
        print("-" * 70)
        
        contagem_impressos = 0
        current_team_context = "MANDANTE" # Começa assumindo o primeiro bloco (geralmente mandante)

        for linha in linhas:
            try:
                # Verifica se a linha atual é na verdade um cabeçalho de seção de time
                html_linha = linha.get_attribute("innerHTML") or ""
                
                # Se a própria linha contiver o seletor de time que você mandou, atualizamos quem está jogando
                if "fp-teamSelector" in html_linha or "wcl-selectButton" in html_linha:
                    try:
                        img_bloco = linha.find_element(By.CSS_SELECTOR, "img")
                        alt_bloco = img_bloco.get_attribute("alt").strip().upper()
                        if alt_bloco:
                            if nome_fora_topo in alt_bloco or "CUIABA" in alt_bloco:
                                current_team_context = "VISITANTE"
                            else:
                                current_team_context = "MANDANTE"
                            print(f"\n STRUTURA | 🔄 Mudando contexto para o bloco do time: {current_team_context} ({alt_bloco})\n")
                    except:
                        pass
                    continue # Pula a linha de cabeçalho, vai para os jogadores

                # Localiza o nome do jogador
                nome_element = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                nome_jogador = nome_element.text.split('\n')[0].strip()
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue

                # Extrai o valor numérico usando o índice mapeado
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                
                if len(celulas) > indice_alvo:
                    valor_chute_alvo = celulas[indice_alvo].text.strip()
                    print(f"👤 Jogador: {nome_jogador.ljust(22)} | 👥 Time Contexto: {current_team_context.ljust(11)} | 🎯 Chutes no Alvo: {valor_chute_alvo}")
                    contagem_impressos += 1
            except:
                continue

        print("-" * 70)
        print(f"✅ Extração concluída. Total de atletas válidos listados: {contagem_impressos}")

    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_finalizacoes()
                        
