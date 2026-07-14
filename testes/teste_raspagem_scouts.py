import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    """Lógica fiel do seu teste isolado."""
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"      🔍 [DEBUG SCOUT] Acessando aba {mercado}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.5)
        
        termos_busca = ["ALVO", "TARGET", "NO GOL"] if mercado == "finalizacoes" else ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
        
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS", "FOULS"]):
                indice_alvo = idx
                break
        
        if indice_alvo == -1: indice_alvo = 5 if mercado == "finalizacoes" else 4

        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_element = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']")
                nome_jogador = nome_element.text.strip()
                
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
        print(f"  ⚠️ Erro na aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    dicionario_escudos = {}
    links_jogos_historico = set()
    acumulador = {}

    try:
        driver.get(url_h2h_mae)
        time.sleep(4.0)
        
        # Mapeamento dinâmico igual ao seu teste isolado
        blocos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        for bloco in blocos_h2h:
            linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
            for linha_jogo in linhas_jogos[:5]:
                href = linha_jogo.get_attribute("href")
                if href: links_jogos_historico.add(href)
                
                participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
                for p in participantes:
                    try:
                        img = p.find_element(By.CSS_SELECTOR, "img")
                        src = img.get_attribute("src").split('/')[-1]
                        nome = p.text.strip().upper()
                        if src and nome and src not in dicionario_escudos:
                            dicionario_escudos[src] = nome
                    except: continue

        lista_final_links = list(links_jogos_historico)[:10]
        
        for url_jogo in lista_final_links:
            mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
            url_base = url_jogo.split("/?")[0].rstrip('/')
            
            extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
            extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

        dados_jogo["historico_chutes"] = acumulador
        dados_jogo["historico_faltas"] = acumulador
        
    except Exception as e:
        print(f"  🚨 Erro crítico na Fase 3: {e}")

    return dados_jogo
    
