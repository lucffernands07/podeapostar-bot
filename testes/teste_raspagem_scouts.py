import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    """
    Função Operária: Foca em uma aba específica, extrai a tabela de jogadores 
    e atualiza o acumulador por referência.
    """
    # Montagem limpa: url_base pura + caminho + mid final
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"      🔍 [DEBUG SCOUT] Acessando aba {mercado}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(4.0)
        
        termos_busca = ["ALVO", "TARGET", "NO GOL"] if mercado == "finalizacoes" else ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
        
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS", "FOULS"]):
                indice_alvo = idx
                break
        
        if indice_alvo == -1:
            indice_alvo = 5 if mercado == "finalizacoes" else 4

        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"      🔍 [DEBUG SCOUT] Linhas encontradas na tabela {mercado}: {len(linhas)}")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']").text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS": continue
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-teamLogo_sFhMr img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                if time_real == "DESCONHECIDO": continue
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    qtd = int(valor_txt) if valor_txt.isdigit() else 0
                    
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
        print(f"  ⚠️ Erro ao processar aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    """
    Função Gerente: Orquestra o H2H, mapeia times e chama a extração.
    """
    if "historico_chutes" not in dados_jogo: dados_jogo["historico_chutes"] = {}
    if "historico_faltas" not in dados_jogo: dados_jogo["historico_faltas"] = {}

    dicionario_escudos = {}
    try:
        participantes = driver.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant']")
        for p in participantes:
            try:
                img = p.find_element(By.CSS_SELECTOR, "img")
                src = img.get_attribute("src").split('/')[-1]
                nome = p.text.strip().upper()
                dicionario_escudos[src] = nome
            except: continue
    except: pass

    links_historico = []
    try:
        blocos = driver.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
        print(f"      🔍 [DEBUG SCOUT] Blocos H2H encontrados: {len(blocos)}")
        for link in blocos[:5]:
            href = link.get_attribute("href")
            if href: links_historico.append(href)
    except Exception as e:
        print(f"      ⚠️ [ERRO SCOUT] Falha ao coletar links: {e}")

    acumulador = {}
    for url_jogo in links_historico:
        if not url_jogo: continue
        
        # AJUSTE: Limpa a base removendo tudo que vem após a URL principal do jogo
        # Exemplo: .../time-a-id/time-b-id/?mid=ID -> vira .../time-a-id/time-b-id
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    dados_jogo["historico_chutes"] = acumulador
    dados_jogo["historico_faltas"] = acumulador
    
    return dados_jogo
                
