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
        
        # LOG INCONDICIONAL: Para você ver que ele está lendo o site
        print(f"     📊 Linhas encontradas na tabela: {len(linhas)}")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], [data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='playerName']").text.strip()
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                valor_txt = celulas[indice_alvo].text.strip() if len(celulas) > indice_alvo else "N/A"
                qtd = int(valor_txt) if valor_txt.isdigit() else 0
                
                # LOG DE AUDITORIA COMPLETO (Vai aparecer mesmo se o time for desconhecido)
                print(f"     👤 Jogador: {nome_jogador:20} | EscudoID: {arquivo_linha} | Time: {time_real} | Qtd: {qtd}")
                
                if time_real != "DESCONHECIDO" and qtd > 0:
                    if nome_jogador not in acumulador_scouts:
                        acumulador_scouts[nome_jogador] = {"time": time_real, "chutes_total": 0, "chutes_jogos": 0, "faltas_total": 0, "faltas_jogos": 0}
                    
                    if mercado == "finalizacoes":
                        acumulador_scouts[nome_jogador]["chutes_total"] += qtd
                        acumulador_scouts[nome_jogador]["chutes_jogos"] += 1
                    else:
                        acumulador_scouts[nome_jogador]["faltas_total"] += qtd
                        acumulador_scouts[nome_jogador]["faltas_jogos"] += 1
            except Exception as e:
                # Opcional: logar erro individual se uma linha estiver mal formatada
                continue
    except Exception as e:
        print(f"  ⚠️ Erro crítico na aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    print("\nINICIANDO TESTE MULTI-MERCADO H2H: CHUTES NO GOL E FALTAS SOFRIDAS")
    print("="*80)
    print(f"🔗 Acessando H2H do confronto: {url_h2h_mae}\n")
    
    driver.get(url_h2h_mae)
    time.sleep(4.0) # Aumentado para garantir carregamento total
    
    dicionario_escudos = {}
    print("📦 Dicionário de Escudos mapeado dinamicamente via H2H:")
    
    # AJUSTE: Buscando pelo contêiner pai estável
    containers = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']")
    
    for container in containers:
        try:
            # AJUSTE: Buscando o item filho pelo prefixo da classe (ignora a ID dinâmica no final)
            item = container.find_element(By.CSS_SELECTOR, "div[class^='wcl-item_']")
            
            img = item.find_element(By.CSS_SELECTOR, "img")
            src = img.get_attribute("src")
            arquivo_id = src.split('/')[-1]
            
            # AJUSTE: Buscando o nome pelo data-testid fixo do span
            nome_time = item.find_element(By.CSS_SELECTOR, "span[data-testid='wcl-scores-simple-text-01']").text.strip().upper()
            
            dicionario_escudos[arquivo_id] = nome_time
            print(f"    • {arquivo_id} ➔ {nome_time}")
        except Exception as e:
            continue

    # AJUSTE: Removido o ':first-child' para capturar todos os jogos listados no H2H
    links_historico = [l.get_attribute("href") for l in driver.find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
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
    
    dados_jogo["historico_chutes"] = acumulador
    dados_jogo["historico_faltas"] = acumulador
    return dados_jogo
