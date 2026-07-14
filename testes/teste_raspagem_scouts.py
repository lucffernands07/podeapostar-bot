import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    mercado_nome = "Chutes no gol" if mercado == "finalizacoes" else "Faltas sofridas"
    
    try:
        driver.get(url_final)
        time.sleep(3.0)
        
        indice_alvo = 5 if mercado == "ataque" else 6
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                # Extração jogador e escudo
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.text.split('\n')[0].strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                # Extração valor
                celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
                valor_txt = celulas[indice_alvo].text.strip() if len(celulas) > indice_alvo else "0"
                qtd = int(valor_txt) if valor_txt.isdigit() else 0
                
                if time_real != "DESCONHECIDO" and qtd > 0:
                    # LOG DOS SCOUTS EXATAMENTE COMO PEDIDO
                    print(f"     👤 Jogador: {nome_jogador:20} | Time: {time_real:10} | {mercado_nome}: {qtd}")
                    
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
        pass # Omitido para não poluir a sua log limpa

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

    # Capturando os blocos de últimos jogos (Mandante = Bloco 0, Visitante = Bloco 1)
    secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
    links_t1 = []
    links_t2 = []
    
    if len(secoes) >= 2:
        links_t1 = [l.get_attribute("href") for l in secoes[0].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
        links_t2 = [l.get_attribute("href") for l in secoes[1].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
    else:
        # Fallback de segurança se a página mudar
        todos_links = [l.get_attribute("href") for l in driver.find_elements(By.CSS_SELECTOR, "a.h2h__row")]
        links_t1 = todos_links[:5]
        links_t2 = todos_links[5:10] if len(todos_links) >= 10 else []

    print("\nlog: A url dos últimos 5 jogos do mandante como os jogos casa x visitante juntos e os scouts de cada jogador")
    acumulador = {}
    
    # Processa os 5 jogos do Mandante (T1)
    for i, url_jogo in enumerate(links_t1, 1):
        print(f"\n{t1} {i}/{len(links_t1)}: {url_jogo}")
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    # Processa os 5 jogos do Visitante (T2)
    for i, url_jogo in enumerate(links_t2, 1):
        print(f"\n{t2} {i}/{len(links_t2)}: {url_jogo}")
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    # Impressão do Resultado Final Estruturado
    print("\n" + "="*50)
    for time_alvo in [t1, t2]:
        print(f"{time_alvo.capitalize()}:")
        jogadores = {k: v for k, v in acumulador.items() if v['time'] == time_alvo.upper()}
        
        # Guardar logs em listas para imprimir Chutes e Faltas separadamente e organizados
        log_chutes = []
        log_faltas = []
        
        for nome, d in jogadores.items():
            m_c = d['chutes'] / d['c_jogos'] if d['c_jogos'] > 0 else 0
            m_f = d['faltas'] / d['f_jogos'] if d['f_jogos'] > 0 else 0
            
            # Se a média for 1.0 ou mais, ela entra (como no seu exemplo do Mbappe com 1.0)
            if m_c >= 1.0: 
                log_chutes.append(f"Chutes no gol: {nome} média {m_c:.1f}")
            if m_f >= 1.0: 
                log_faltas.append(f"Faltas sofridas: {nome} média {m_f:.1f}")
                
        for linha in log_chutes:
            print(linha)
        for linha in log_faltas:
            print(linha)

    return dados_jogo
