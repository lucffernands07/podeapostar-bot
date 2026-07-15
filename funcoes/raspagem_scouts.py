#funcoes/raspagem_scouts.py

import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    """Navega na aba específica (finalizacoes ou ataque) e extrai o scout correspondente usando seletores de alta fidelidade."""
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    mercado_nome = "Finalizações no alvo" if mercado == "finalizacoes" else "Faltas sofridas"
    
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.5) # Tempo ideal do seu teste isolado para renderização da tabela
        
        # Define os termos de busca no cabeçalho baseados no mercado
        termos_busca = ["ALVO", "TARGET", "NO GOL"] if mercado == "finalizacoes" else ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
        
        # Identifica dinamicamente o índice da coluna
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS", "FOULS"]):
                indice_alvo = idx
                break
        
        # Se não achar dinamicamente, usa os índices padrão do Flashscore
        if indice_alvo == -1:
            indice_alvo = 5 if mercado == "finalizacoes" else 4

        # Seletores extraídos do seu teste isolado de sucesso
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                # Seletores robustos de célula de jogador e logo do teste isolado
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_element = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']")
                nome_jogador = nome_element.text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-teamLogo_sFhMr img")
                src_linha = img_logo.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                if time_real == "DESCONHECIDO":
                    continue
                
                # Coleta as células e captura os valores numéricos
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    qtd = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    # LOG DE AUDITORIA COMPLETO DURANTE A VARREDURA
                    print(f"     👤 Jogador: {nome_jogador:20} | EscudoID: {arquivo_linha} | Time: {time_real} | {mercado_nome}: {qtd}")
                    
                    if qtd > 0:
                        if nome_jogador not in acumulador_scouts:
                            acumulador_scouts[nome_jogador] = {
                                "time": time_real, 
                                "chutes": 0, "c_jogos": 0,
                                "faltas": 0, "f_jogos": 0
                            }
                        
                        if mercado == "finalizacoes":
                            acumulador_scouts[nome_jogador]["chutes"] += qtd
                            acumulador_scouts[nome_jogador]["c_jogos"] += 1
                        else:
                            acumulador_scouts[nome_jogador]["faltas"] += qtd
                            acumulador_scouts[nome_jogador]["f_jogos"] += 1
            except:
                continue
    except Exception as e:
        print(f"  ⚠️ Erro ao processar aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    
    print("\nFase 3:")
    print(f"log: url h2h do confronto {t1} x {t2}")
    print(url_h2h_mae)
    
    driver.get(url_h2h_mae)
    time.sleep(4.0)
    
    print(f"\nlog: os ids dos pngs capturados dos times do histórico na pagina h2h")
    dicionario_escudos = {}
    links_jogos_historico = set()
    acumulador_scouts = {}
    
    # Isola as duas primeiras seções (Mandante e Visitante) para evitar confronto direto
    secoes_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
    
    # Varre estritamente as primeiras duas tabelas (Mandante e Visitante)
    for bloco in secoes_h2h[:2]:
        linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
        for linha_jogo in linhas_jogos[:5]: # Máximo de 5 jogos de cada
            href = linha_jogo.get_attribute("href")
            if href:
                links_jogos_historico.add(href)
            
            participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
            for p in participantes:
                try:
                    img_el = p.find_element(By.CSS_SELECTOR, "img")
                    src_img = img_el.get_attribute("src") or ""
                    nome_arquivo = src_img.split('/')[-1]
                    nome_time = p.text.strip().upper()
                    if nome_arquivo and nome_time and nome_arquivo not in dicionario_escudos:
                        dicionario_escudos[nome_arquivo] = nome_time
                except:
                    continue

    print(f"\n📦 Dicionário de Escudos mapeado dinamicamente via H2H ({len(dicionario_escudos)} times):")
    for png, time_nome in dicionario_escudos.items():
        print(f"    • {png} ➔ {time_nome}")
        
    lista_final_links = list(links_jogos_historico)[:10]
    print(f"\n🔗 Total de jogos únicos para varrer (máximo 10): {len(lista_final_links)}")
    print("-" * 80)

    # Varre cada um dos jogos coletados executando os dois mercados por jogo
    for idx, url_jogo in enumerate(lista_final_links, start=1):
        print(f"实用 Processando jogo [{idx}/{len(lista_final_links)}]")
        
        if "?mid=" in url_jogo:
            parts = url_jogo.split("?mid=")
            url_base = parts[0].rstrip('/')
            mid_param = parts[1]
        else:
            url_base = url_jogo.split("/#")[0].rstrip('/')
            mid_param = ""

        # Extrai mercado 1: Chutes no Alvo
        extrair_scouts_por_aba(driver, url_base, mid_param, "finalizacoes", dicionario_escudos, acumulador_scouts)
        # Extrai mercado 2: Faltas Sofridas
        extrair_scouts_por_aba(driver, url_base, mid_param, "ataque", dicionario_escudos, acumulador_scouts)
        print("-" * 60)

    # 🟢 LOG DE AUDITORIA DE AMOSTRA DE RETORNO DO DICIONÁRIO INTEGRADO
    print("\n" + "="*60)
    print("📊 [VALIDAÇÃO DE DADOS DE JOGADORES INTEGRADOS COM SUCESSO]")
    amostra_finalizacao = None
    amostra_falta = None
    
    for jogador, info in acumulador_scouts.items():
        if info["chutes"] > 0 and not amostra_finalizacao:
            amostra_finalizacao = (jogador, info)
        if info["faltas"] > 0 and not amostra_falta:
            amostra_falta = (jogador, info)
        if amostra_finalizacao and amostra_falta:
            break

    if amostra_finalizacao:
        print(f"  🎯 CHUTES NO ALVO: {amostra_finalizacao[0]} | Time: {amostra_finalizacao[1]['time']} | Total: {amostra_finalizacao[1]['chutes']} em {amostra_finalizacao[1]['c_jogos']} jogo(s)")
    if amostra_falta:
        print(f"  🤕 FALTAS SOFRIDAS: {amostra_falta[0]} | Time: {amostra_falta[1]['time']} | Total: {amostra_falta[1]['faltas']} em {amostra_falta[1]['f_jogos']} jogo(s)")
    print("="*60 + "\n")

    return acumulador_scouts
            

                                                
                    
