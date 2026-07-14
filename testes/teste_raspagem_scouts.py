import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts, idx_jogo, total_jogos):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.0)
        
        indice_alvo = 5 if mercado == "finalizacoes" else 4
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='playerName']").text.strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    qtd = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    if time_real != "DESCONHECIDO" and qtd > 0:
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
    print("\nINICIANDO TESTE MULTI-MERCADO H2H: CHUTES NO GOL E FALTAS SOFRIDAS")
    print("="*80)
    print(f"🔗 Acessando H2H do confronto: {url_h2h_mae}\n")
    
    driver.get(url_h2h_mae)
    time.sleep(3.0)
    
    dicionario_escudos = {}
    participantes = driver.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant']")
    print("📦 Dicionário de Escudos mapeado dinamicamente via H2H:")
    for p in participantes:
        try:
            img = p.find_element(By.CSS_SELECTOR, "img")
            src = img.get_attribute("src").split('/')[-1]
            nome_time = p.text.strip().upper()
            dicionario_escudos[src] = nome_time
            print(f"    • {src} ➔ {nome_time}")
        except: continue

    links_historico = [l.get_attribute("href") for l in driver.find_elements(By.CSS_SELECTOR, ".h2h__section:first-child a.h2h__row")][:5]
    print(f"\n🔗 Total de jogos únicos para varrer: {len(links_historico)}")
    print("-" * 80)

    acumulador = {}
    for i, url_jogo in enumerate(links_historico, 1):
        print(f"实用 Processando jogo [{i}/{len(links_historico)}]")
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador, i, len(links_historico))
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador, i, len(links_historico))
        print("-" * 60)

    print("\n" + "="*80)
    print("📊 PROCESSAMENTO FINAL DAS MÉDIAS (REQUISITO: MÉDIA >= 1.0)")
    print("="*80)
    
    # Aqui você imprimiria o resumo do seu 'acumulador'
    print(f"\n🏁 FIM DO TESTE COMPLETO DE SCOUTS COMBINADOS")
    
    dados_jogo["historico_chutes"] = acumulador
    dados_jogo["historico_faltas"] = acumulador
    return dados_jogo
