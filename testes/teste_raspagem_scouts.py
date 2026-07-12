# testes/teste_raspagem_scouts.py

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_scouts_avancados(driver, stats, t1, t2):
    url_h2h_base = stats.get("url_h2h_base")
    print(f"         [RASPAGEM 3] Iniciou. URL Recebida: {url_h2h_base}")

    if not url_h2h_base:
        url_h2h_base = driver.current_url if "h2h" in driver.current_url else None
        print(f"         [RASPAGEM 3] Tentativa de recuperar URL atual: {url_h2h_base}")

    if not url_h2h_base:
        print("         🚨 [RASPAGEM 3] Abortando: url_h2h_base é nula!")
        return stats

    if "historico_chutes" not in stats: stats["historico_chutes"] = {}
    if "historico_faltas" not in stats: stats["historico_faltas"] = {}
    if "elenco_mandante" not in stats: stats["elenco_mandante"] = []
    if "elenco_visitante" not in stats: stats["elenco_visitante"] = []

    wait = WebDriverWait(driver, 10)

    # 🟢 CAPTURA DE ELENCOS
    try:
        url_escalacoes = url_h2h_base.replace("/h2h/overall", "/escalacoes")
        print(f"         [RASPAGEM 3] Acessando Elencos: {url_escalacoes}")
        driver.get(url_escalacoes)
        time.sleep(2.5)
        
        jogadores_casa = driver.find_elements(By.CSS_SELECTOR, "[class*='home'] [class*='participantName'], .lf__side--home [class*='participantName']")
        print(f"         [RASPAGEM 3] Elementos de jogadores casa achados: {len(jogadores_casa)}")
        for j in jogadores_casa:
            nome = driver.execute_script("return arguments[0].textContent;", j).strip()
            if nome and nome not in stats["elenco_mandante"]: stats["elenco_mandante"].append(nome)
            
        jogadores_fora = driver.find_elements(By.CSS_SELECTOR, "[class*='away'] [class*='participantName'], .lf__side--away [class*='participantName']")
        print(f"         [RASPAGEM 3] Elementos de jogadores fora achados: {len(jogadores_fora)}")
        for j in jogadores_fora:
            nome = driver.execute_script("return arguments[0].textContent;", j).strip()
            if nome and nome not in stats["elenco_visitante"]: stats["elenco_visitante"].append(nome)
    except Exception as e_elenco:
        print(f"         ⚠️ Erro ao mapear elencos: {e_elenco}")

    jogo_global_index = 0
    secoes_alvo_scouts = [
        {"tipo": "MANDANTE", "idx_secao": 1},
        {"tipo": "VISITANTE", "idx_secao": 2}
    ]

    try:
        for alvo in secoes_alvo_scouts:
            lista_urls_jogos = []
            try:
                print(f"         [RASPAGEM 3] Listando confrontos para seção {alvo['tipo']}...")
                driver.get(url_h2h_base)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                print(f"         [RASPAGEM 3] Linhas encontradas na seção: {len(linhas_confrontos)}")
                
                for jogo_idx in range(min(3, len(linhas_confrontos))):
                    try:
                        elemento_alvo = linhas_confrontos[jogo_idx]
                        mandante_atual = elemento_alvo.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
                        visitante_atual = elemento_alvo.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
                        
                        lista_urls_jogos.append({
                            "idx": jogo_idx,
                            "mandante_atual": mandante_atual,
                            "visitante_atual": visitante_atual
                        })
                    except Exception as e_row:
                        print(f"         ⚠️ Erro na linha index {jogo_idx}: {e_row}")
                        continue
            except Exception as e_coleta:
                print(f"         ⚠️ Erro ao listar linhas para scouts: {e_coleta}")
                continue

            print(f"         [RASPAGEM 3] Total de jogos históricos mapeados para processar: {len(lista_urls_jogos)}")
            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(url_h2h_base)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    
                    selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]
                    
                    mandante_atual = jogo_dados["mandante_atual"]
                    visitante_atual = jogo_dados["visitante_atual"]

                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", elemento_alvo)
                    
                    try: WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                    except: pass
                        
                    time.sleep(2.5)
                    url_jogo_completa = driver.current_url.split("?")[0].strip("/")
                    print(f"         [RASPAGEM 3] Entrou no jogo histórico: {url_jogo_completa}")

                    hash_mandante_topo, hash_visitante_topo = "", ""
                    try:
                        img_m = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image, [class*='homeLogo'] img")
                        hash_mandante_topo = img_m.get_attribute("src").split('/')[-1]
                        img_v = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image, [class*='awayLogo'] img")
                        hash_visitante_topo = img_v.get_attribute("src").split('/')[-1]
                    except: pass
                    
                    # 🎯 PASSO 2: Coleta de Chutes (Corrigido para nova estrutura)
                    url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
                    print(f"         [RASPAGEM 3] Navegando para Finalizações: {url_finalizacoes}")
                    driver.get(url_finalizacoes)
                    
                    try:
                        driver.execute_script("window.scrollTo(0, 300);")
                        time.sleep(2.0) # Um pouquinho mais de tempo para renderizar a tabela
                        
                        # Captura cabeçalhos antigos ou novos com data-testid
                        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
                        indice_chutes = 5  
                        for idx_th, th in enumerate(cabecalhos_fin):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            if any(x in texto_th for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in texto_th for x in ["XG", "XGOT"]):
                                indice_chutes = idx_th
                                break
                    
                        # Seleção robusta das linhas da tabela
                        linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
                        print(f"         [RASPAGEM 3] Linhas de dados de chutes achadas: {len(linhas_dados_fin)}")
                        
                        for lambda_linha in linhas_dados_fin:
                            try:
                                try:
                                    nome_element = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                                except: continue
                                    
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                                if not nome_jogador or nome_jogador == "TODOS": continue
                                
                                try:
                                    img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='teamLogo'] img, [class*='wcl-teamLogo'] img, img")
                                    hash_linha = img_linha.get_attribute("src").split('/')[-1]
                                    
                                    time_identificado = ""
                                    if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                                    elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                                    else: continue 
                                    
                                    if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                                        continue
                                except: continue

                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                                if len(celulas_valores) <= indice_chutes: continue
                                
                                val_chute = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes]).strip()
                                chutes = int(re.search(r'\d+', val_chute).group()) if re.search(r'\d+', val_chute) else 0
                    
                                if nome_jogador not in stats["historico_chutes"]: stats["historico_chutes"][nome_jogador] = []
                                while len(stats["historico_chutes"][nome_jogador]) < jogo_global_index: stats["historico_chutes"][nome_jogador].append(0)
                                stats["historico_chutes"][nome_jogador].append(chutes)
                            except: continue
                    except Exception as e_passo2:
                        print(f"         ⚠️ Erro ao processar finalizações: {e_passo2}")

                    # 🎯 PASSO 3: Coleta de Faltas (Corrigido para nova estrutura)
                    url_ataque = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
                    print(f"         [RASPAGEM 3] Navegando para Ataque: {url_ataque}")
                    driver.get(url_ataque)
                    
                    try:
                        driver.execute_script("window.scrollTo(0, 300);")
                        time.sleep(2.0)
                        
                        cabecalhos_atq = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
                        indice_faltas = 5  
                        for idx_th, th in enumerate(cabecalhos_atq):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            if any(x in texto_th for x in ["SOFRIDAS", "FALTAS SOFRIDAS", "FOULS SUFFERED", "FS"]):
                                indice_faltas = idx_th
                                break
                    
                        # Seleção robusta das linhas da tabela
                        linhas_dados_atq = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
                        print(f"         [RASPAGEM 3] Linhas de dados de ataque achadas: {len(linhas_dados_atq)}")
                        
                        for lambda_linha in linhas_dados_atq:
                            try:
                                try:
                                    nome_element = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                                except: continue
                                    
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                                if not nome_jogador or nome_jogador == "TODOS": continue
                                
                                try:
                                    img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='teamLogo'] img, [class*='wcl-teamLogo'] img, img")
                                    hash_linha = img_linha.get_attribute("src").split('/')[-1]
                                    
                                    time_identificado = ""
                                    if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                                    elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                                    else: continue 
                                    
                                    if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                                        continue
                                except: continue

                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                                if len(celulas_valores) <= indice_faltas: continue
                                
                                val_falta = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_faltas]).strip()
                                faltas_sof = int(re.search(r'\d+', val_falta).group()) if re.search(r'\d+', val_falta) else 0
                    
                                if nome_jogador not in stats["historico_faltas"]: stats["historico_faltas"][nome_jogador] = []
                                while len(stats["historico_faltas"][nome_jogador]) < jogo_global_index: stats["historico_faltas"][nome_jogador].append(0)
                                stats["historico_faltas"][nome_jogador].append(faltas_sof)
                            except: continue
                    except Exception as e_passo3:
                        print(f"         ⚠️ Erro ao processar faltas sofridas: {e_passo3}")
                    jogo_global_index += 1
                except Exception as e_loop_jogo:
                    print(f"         ⚠️ Erro no loop do jogo histórico: {e_loop_jogo}")
                    continue
    except Exception as e:
        print(f"      ⚠️ Erro Crítico na Raspagem Geral: {e}")

    for jogador, lista in stats["historico_chutes"].items():
        while len(lista) < jogo_global_index: lista.append(0)
    for jogador, lista in stats["historico_faltas"].items():
        while len(lista) < jogo_global_index: lista.append(0)

    print(f"         [RASPAGEM 3] Finalizada com sucesso. Jogos processados: {jogo_global_index}")
    return stats
                            
                                            
                                
