import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"      🔍 [DEBUG] Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.0)
        
        # Identificação de Colunas
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = 5 if mercado == "finalizacoes" else 4
        
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"      📊 [DEBUG] Linhas encontradas: {len(linhas)}")
        
        for linha in linhas:
            try:
                # Extração jogador e time
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']").text.strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-table__cellPlayerTeamLogo")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    qtd = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    if time_real != "DESCONHECIDO" and qtd > 0:
                        print(f"      ✅ [DEBUG] {nome_jogador} ({time_real}) | QTD: {qtd}")
                        if nome_jogador not in acumulador_scouts:
                            acumulador_scouts[nome_jogador] = {"time": time_real, "chutes_total": 0, "chutes_jogos": 0, "faltas_total": 0, "faltas_jogos": 0}
                        
                        if mercado == "finalizacoes":
                            acumulador_scouts[nome_jogador]["chutes_total"] += qtd
                            acumulador_scouts[nome_jogador]["chutes_jogos"] += 1
                        else:
                            acumulador_scouts[nome_jogador]["faltas_total"] += qtd
                            acumulador_scouts[nome_jogador]["faltas_jogos"] += 1
            except: continue
    except Exception as e:
        print(f"  ⚠️ Erro na aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    driver.get(url_h2h_mae)
    time.sleep(3.0)
    
    dicionario_escudos = {}
    
    # 1. Mapear escudos apenas da página atual de H2H
    participantes = driver.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant']")
    for p in participantes:
        try:
            img = p.find_element(By.CSS_SELECTOR, "img")
            dicionario_escudos[img.get_attribute("src").split('/')[-1]] = p.text.strip().upper()
        except: continue

    # 2. Capturar APENAS os 5 últimos jogos do confronto direto (H2H)
    links_historico = []
    # O Flashscore tem blocos de "Jogos Recentes". O primeiro bloco costuma ser o H2H.
    blocos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
    if blocos:
        linhas = blocos[0].find_elements(By.CSS_SELECTOR, "a.h2h__row")
        for linha in linhas[:5]: # Apenas os 5 últimos
            href = linha.get_attribute("href")
            if href: links_historico.append(href)
            
    print(f"      🎯 [DEBUG] Jogos H2H encontrados para análise: {len(links_historico)}")

    acumulador = {}
    for url_jogo in links_historico:
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    dados_jogo["historico_chutes"] = acumulador
    dados_jogo["historico_faltas"] = acumulador
    return dados_jogo
    
