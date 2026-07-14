import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.0)
        
        # AJUSTE 1: Mapeamento preciso por mercado
        # Em finalizações (chutes) geralmente é o 5º índice. Em "Ataque" (faltas sofridas) é o 4º.
        indice_alvo = 5 if mercado == "finalizacoes" else 4
        
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"     📊 Linhas encontradas na tabela: {len(linhas)}")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='playerName']").text.strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                valor_txt = celulas[indice_alvo].text.strip() if len(celulas) > indice_alvo else "0"
                qtd = int(valor_txt) if valor_txt.isdigit() else 0
                
                # LOG DE AUDITORIA (Mantido como você pediu)
                print(f"     👤 Jogador: {nome_jogador:20} | EscudoID: {arquivo_linha} | Time: {time_real} | Qtd: {qtd}")
                
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
        print(f"  ⚠️ Erro na aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    print("\nINICIANDO TESTE MULTI-MERCADO H2H: CHUTES NO GOL E FALTAS SOFRIDAS")
    print("="*80)
    
    driver.get(url_h2h_mae)
    time.sleep(4.0)
    
    # Mapeamento dinâmico (com ajuste do contêiner estável)
    dicionario_escudos = {}
    containers = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']")
    for c in containers:
        try:
            item = c.find_element(By.CSS_SELECTOR, "div[class^='wcl-item_']")
            src = item.find_element(By.CSS_SELECTOR, "img").get_attribute("src").split('/')[-1]
            nome = item.find_element(By.CSS_SELECTOR, "span[data-testid='wcl-scores-simple-text-01']").text.strip().upper()
            dicionario_escudos[src] = nome
            print(f"    • {src} ➔ {nome}")
        except: continue

    # AJUSTE 3: Removido [:5] para varrer todos os jogos do histórico (Mandante + Visitante)
    links_historico = [l.get_attribute("href") for l in driver.find_elements(By.CSS_SELECTOR, "a.h2h__row")]
    print(f"\n🔗 Total de jogos únicos para varrer: {len(links_historico)}")

    acumulador = {}
    for url_jogo in links_historico:
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    # AJUSTE 2: Log final com média >= 1.0 (O que você queria ver)
    print("\n" + "="*80)
    print("📊 PROCESSAMENTO FINAL DAS MÉDIAS (REQUISITO: MÉDIA >= 1.0)")
    for nome, dados in acumulador.items():
        m_chutes = dados["chutes"] / dados["c_jogos"] if dados["c_jogos"] > 0 else 0
        m_faltas = dados["faltas"] / dados["f_jogos"] if dados["f_jogos"] > 0 else 0
        
        if m_chutes >= 1.0:
            print(f"🎯 Destaque Chutes: {nome} ({dados['time']}) - Média: {m_chutes:.2f}")
        if m_faltas >= 1.0:
            print(f"⚠️ Destaque Faltas: {nome} ({dados['time']}) - Média: {m_faltas:.2f}")

    print("\n🏁 FIM DO TESTE COMPLETO")
    dados_jogo["historico_chutes"] = acumulador
    dados_jogo["historico_faltas"] = acumulador
    return dados_jogo
                        
