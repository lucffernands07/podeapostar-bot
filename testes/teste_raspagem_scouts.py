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
                celula_jogador = inline = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .playerCell")
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
    
    # 🔴 TRAVA DOS PNGS: Isola estritamente as duas primeiras seções (Mandante e Visitante)
    # Ignora totalmente a terceira seção (Confronto Direto/Mutual) para não misturar os times
    secoes_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
    participantes_validos = []
    
    if len(secoes_h2h) >= 2:
        for sec in secoes_h2h[:2]:
            participantes_validos.extend(sec.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']"))
    else:
        # Fallback de segurança se as seções não renderizarem (limita aos 20 primeiros elementos = 10 jogos)
        participantes_validos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']")[:20]

    for c in participantes_validos:
        try:
            img = c.find_element(By.CSS_SELECTOR, "img")
            src = img.get_attribute("src").split('/')[-1]
            nome = c.find_element(By.CSS_SELECTOR, "span[data-testid='wcl-scores-simple-text-01']").text.strip().upper()
            
            # Alimenta o dicionário limitando para evitar duplicados indesejados
            if src not in dicionario_escudos:
                dicionario_escudos[src] = nome
                print(f"{src} ➔ {nome}")
        except: continue

    # Separação dos blocos H2H (5 do mandante e 5 do visitante)
    links_t1 = []
    links_t2 = []
    
    if len(secoes_h2h) >= 2:
        links_t1 = [l.get_attribute("href") for l in secoes_h2h[0].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
        links_t2 = [l.get_attribute("href") for l in secoes_h2h[1].find_elements(By.CSS_SELECTOR, "a.h2h__row")][:5]
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

    # 🟢 NOVO LOG DE VALIDAÇÃO: Amostra detalhada do acumulador antes do retorno
    print("\n" + "="*60)
    print("📊 [VALIDAÇÃO DE DADOS DE JOGADORES COLETADOS] Amostra do Acumulador:")
    
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
        print(f"  🎯 FINALIZAÇÕES NO ALVO: {amostra_finalizacao[0]} | Time: {amostra_finalizacao[1]['time']} | Total Chutes: {amostra_finalizacao[1]['chutes']} em {amostra_finalizacao[1]['c_jogos']} jogo(s)")
    else:
        print("  🎯 FINALIZAÇÕES NO ALVO: Nenhum jogador com registros maiores que zero.")

    if amostra_falta:
        print(f"  🤕 FALTAS SOFRIDAS: {amostra_falta[0]} | Time: {amostra_falta[1]['time']} | Total Faltas: {amostra_falta[1]['faltas']} em {amostra_falta[1]['f_jogos']} jogo(s)")
    else:
        print("  🤕 FALTAS SOFRIDAS: Nenhum jogador com registros maiores que zero.")
    print("="*60 + "\n")

    return acumulador_scouts
    
