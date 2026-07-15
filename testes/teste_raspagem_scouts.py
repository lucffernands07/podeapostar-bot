# testes/teste_raspagem_scouts.py
import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    mercado_nome = "Finalizações no alvo" if mercado == "finalizacoes" else "Faltas sofridas"
    
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(4.0) # Tempo dinâmico para garantir o carregamento da tabela
        
        # --- DESCOBERTA DINÂMICA DO ÍNDICE DA COLUNA ---
        indice_alvo = 5 if mercado == "ataque" else 6 # Fallback padrão seu
        
        # Seletores compatíveis com a estrutura Desktop/Mobile do Flashscore
        headers = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeaderCell'], .tableHeaderCell, th")
        if headers:
            textos_headers = [h.text.strip().lower() for h in headers if h.text.strip()]
            for idx, texto in enumerate(textos_headers):
                if mercado == "finalizacoes" and ("finalizações no alvo" in texto or "finalizações" in texto or "no alvo" in texto):
                    indice_alvo = idx - 1  # Remove 1 pois a lista tableBodyCell não inclui o nome do jogador
                    break
                elif mercado == "ataque" and ("faltas sofridas" in texto or "sofridas" in texto or "faltas recebidas" in texto):
                    indice_alvo = idx - 1
                    break
        
        # Localiza as linhas da tabela
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow'], .tableRow")
        print(f"     📊 Linhas encontradas na tabela: {len(linhas)}")
        
        for linha in linhas:
            try:
                # Extração do jogador e escudo
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .playerCell")
                nome_jogador = celula_jogador.text.split('\n')[0].strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                # Extração do valor com base no índice mapeado
                celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell'], .tableBodyCell")
                valor_txt = celulas[indice_alvo].text.strip() if len(celulas) > indice_alvo else "0"
                qtd = int(valor_txt) if valor_txt.isdigit() else 0
                
                # LOG DE AUDITORIA COMPLETO DURANTE A VARREDURA
                print(f"     👤 Jogador: {nome_jogador:20} | EscudoID: {arquivo_linha} | Time: {time_real} | {mercado_nome}: {qtd}")
                
                if time_real != "DESCONHECIDO" and qtd > 0:
                    if nome_jogador not in acumulador_scouts:
                        acumulador_scouts[nome_jogador] = {"time": time_real, "chutes": 0, "c_jogos": 0, "faltas": 0, "f_jogos": 0}
                    
                    if mercado == "finalizacoes":
                        acumulador_scouts[nome_jogador]["chutes"] += qtd
                        acumulador_scouts[nome_jogador]["c_jogos"] += 1
                    else:
                        acumulador_scouts[nome_jogador]["faltas"] += qtd
                        acumulador_scouts[nome_jogador]["f_jogos"] += 1
            except: continue
    except Exception as e:
        print(f"  ⚠️ Erro na extração da aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    
    print("\nFase 3:")
    print(f"log: url h2h do confronto {t1} x {t2}")
    print(url_h2h_mae)
    
    driver.get(url_h2h_mae)
    time.sleep(4.0)
    
    print(f"\nlog: os ids dos pngs capturados dos times do histórico na pagina h2h")
    dicionario_escudos = {}
    for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']"):
        try:
            img = c.find_element(By.CSS_SELECTOR, "img")
            src = img.get_attribute("src").split('/')[-1]
            nome = c.find_element(By.CSS_SELECTOR, "span[data-testid='wcl-scores-simple-text-01']").text.strip().upper()
            dicionario_escudos[src] = nome
            print(f"{src} ➔ {nome}")
        except: continue

    # Separação dos blocos H2H (5 do mandante e 5 do visitante)
    secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
    links_t1 = []
    links_t2 = []
    
    if len(secoes) >= 2:
        links_t1 = [l.get_attribute("href") for l in secoes[0].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
        links_t2 = [l.get_attribute("href") for l in secoes[1].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
    else:
        todos_links = [l.get_attribute("href") for l in driver.find_elements(By.CSS_SELECTOR, "a.h2h__row")]
        links_t1 = todos_links[:5]
        links_t2 = todos_links[5:10] if len(todos_links) >= 10 else []

    print("\nlog: A url dos últimos 5 jogos do mandante como os jogos casa x visitante juntos e os scouts de cada jogador")
    acumulador_scouts = {}
    
    # Processa histórico do Mandante (T1)
    for i, url_jogo in enumerate(links_t1, 1):
        print(f"\n{t1} {i}/{len(links_t1)}:")
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador_scouts)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador_scouts)

    # Processa histórico do Visitante (T2)
    for i, url_jogo in enumerate(links_t2, 1):
        print(f"\n{t2} {i}/{len(links_t2)}:")
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador_scouts)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador_scouts)

    return acumulador_scouts
    
