import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_scouts_avancados(driver, stats, t1, t2):
    """
    RASPAGEM 2: Varre as subpáginas dos últimos jogos na aba de jogadores.
    """
    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except: pass
        return stats

    try:
        wait = WebDriverWait(driver, 10)
        jogo_global_index = 0
        secoes_alvo_scouts = [
            {"tipo": "MANDANTE", "idx_secao": 1},
            {"tipo": "VISITANTE", "idx_secao": 2}
        ]

        for alvo in secoes_alvo_scouts:
            lista_urls_jogos = []
            try:
                driver.get(url_h2h_base)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                
                for jogo_idx in range(min(3, len(linhas_confrontos))):
                    try:
                        elemento_alvo = linhas_confrontos[jogo_idx]
                        partes_texto = elemento_alvo.text.split('\n')
                        mandante_atual = partes_texto[2].strip() if len(partes_texto) > 2 else ""
                        visitante_atual = partes_texto[3].strip() if len(partes_texto) > 3 else ""
                        
                        lista_urls_jogos.append({
                            "idx": jogo_idx,
                            "mandante_atual": mandante_atual,
                            "visitante_atual": visitante_atual,
                            "elemento": elemento_alvo
                        })
                    except: continue
            except Exception as e_coleta:
                print(f"      ⚠️ Erro ao listar linhas para scouts: {e_coleta}")
                continue

            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(url_h2h_base)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    
                    selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                    if len(linhas_atualizadas) <= jogo_dados["idx"]: continue
                    
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]
                    mandante_atual = jogo_dados["mandante_atual"]
                    visitante_atual = jogo_dados["visitante_atual"]

                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", elemento_alvo)
                    
                    try:
                        WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                    except: pass
                        
                    time.sleep(2.5)
                    url_jogo_completa = driver.current_url.split("?")[0].strip("/")

                    hash_mandante_topo, hash_visitante_topo = "", ""
                    try:
                        img_m = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image")
                        hash_mandante_topo = img_m.get_attribute("src").split('/')[-1]
                        img_v = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image")
                        hash_visitante_topo = img_v.get_attribute("src").split('/')[-1]
                    except: pass

                    # 🗂️ PASSO 1: Coleta de Cartões (Aba Gerais)
                    url_gerais = f"{url_jogo_completa}/resumo/estatisticas-jogadores/gerais/"
                    driver.get(url_gerais)
                    
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                        time.sleep(1.2)
                        
                        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
                        indice_amarelos, indice_vermelhos = -1, -1
                        for idx_th, th in enumerate(cabecalhos):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            alias = str(th.get_attribute("data-analytics-alias")).upper()
                            if "AMARELO" in texto_th or alias == "YELLOW_CARDS" or texto_th == "CA":
                                indice_amarelos = idx_th
                            if "VERMELHO" in texto_th or alias == "RED_CARDS" or texto_th == "CV":
                                indice_vermelhos = idx_th

                        linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                        for lambda_linha in linhas_dados:
                            try:
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", lambda_linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                                if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                                    continue
                                
                                try:
                                    img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='wcl-teamLogo'] img")
                                    hash_linha = img_linha.get_attribute("src").split('/')[-1]
                                except: hash_linha = ""

                                if hash_linha and hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                                elif hash_linha and hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                                else: continue

                                if t1.upper() in time_identificado.upper():
                                    dicionario_am, dicionario_vm = stats["historico_mandante_am"], stats["historico_mandante_vm"]
                                elif t2.upper() in time_identificado.upper():
                                    dicionario_am, dicionario_vm = stats["historico_visitante_am"], stats["historico_visitante_vm"]
                                else: continue

                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                                if not celulas_valores: continue

                                idx_am = indice_amarelos if indice_amarelos != -1 else (len(celulas_valores) - 3)
                                idx_vm = indice_vermelhos if indice_vermelhos != -1 else (len(celulas_valores) - 2)

                                val_amarelo = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_am]).strip()
                                val_vermelho = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_vm]).strip()
                                
                                amarelos = 0 if val_amarelo in ["-", ""] or not val_amarelo.replace(r'\D', '').isdigit() else int(re.sub(r'\D', '', val_amarelo))
                                vermelhos = 0 if val_vermelho in ["-", ""] or not val_vermelho.replace(r'\D', '').isdigit() else int(re.sub(r'\D', '', val_vermelho))
                                
                                if nome_jogador not in dicionario_am: dicionario_am[nome_jogador] = []
                                while len(dicionario_am[nome_jogador]) < jogo_global_index: dicionario_am[nome_jogador].append(0)
                                dicionario_am[nome_jogador].append(amarelos)
                                
                                if nome_jogador not in dicionario_vm: dicionario_vm[nome_jogador] = []
                                while len(dicionario_vm[nome_jogador]) < jogo_global_index: dicionario_vm[nome_jogador].append(0)
                                dicionario_vm[nome_jogador].append(vermelhos)
                            except: continue
                    except: pass
                        
                    # 🎯 PASSO 2: Coleta de Chutes no Alvo (Aba Finalizações)
                    url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
                    try:
                        driver.get(url_finalizacoes)
                        try:
                            elemento_aba_fin = driver.find_element(By.XPATH, "//a[contains(@href, 'finalizacoes')]")
                            driver.execute_script("arguments[0].click();", elemento_aba_fin)
                        except: pass 
                    
                        wait.until(lambda d: any(
                            "FN" in el.text.upper() or "ALVO" in el.text.upper() or "SHOTS" in el.text.upper()
                            for el in d.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
                        ))
                        
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                    
                        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
                        indice_chutes = -1
                        
                        # 1. Tenta encontrar pelo Alias ou Nome
                        for idx_th, th in enumerate(cabecalhos_fin):
                            alias = str(th.get_attribute("data-analytics-alias")).upper()
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            if "SHOTS_ON_TARGET" in alias or "FINALIZAÇÕES NO ALVO" in texto_th or "FN" in texto_th:
                                indice_chutes = idx_th + 1
                                print(f"  ✅ [DEBUG] Coluna encontrada via busca no índice: {idx_th}")
                                break
                                
                        # 2. SE NÃO ACHOU, testa índices conhecidos em vez de cravar no 4
                        if indice_chutes == -1:
                            print("  🔍 [DEBUG] Buscando coluna por tentativa e erro...")
                            # Lista de índices que você sabe que costumam ser a coluna de chutes
                            tentativas = [5, 6, 7, 8, 9, 10]
                            for idx_teste in tentativas:
                                if idx_teste < len(cabecalhos_fin):
                                    val_teste = driver.execute_script("return arguments[0].textContent;", cabecalhos_fin[idx_teste]).strip().upper()
                                    # Verifica se nesta coluna há um número ou se ela parece conter dados de chute
                                    if "FINALIZAÇÕES" in val_teste or "ALVO" in val_teste or "SOT" in val_teste:
                                        indice_chutes = idx_teste
                                        print(f"  ✅ [DEBUG] Coluna encontrada via tentativa no índice: {idx_teste}")
                                        break
                                        
                        # 3. Última salvaguarda
                        if indice_chutes == -1:
                            indice_chutes = 5 # O seu índice de confiança
                            print(f"  ⚠️ [DEBUG] Não achou, usando fallback forçado: {indice_chutes}")
 
                    
                        linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                        for lambda_linha in linhas_dados_fin:
                            try:
                                nome_element = lambda_linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName']")
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                                if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper(): continue
                                
                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                                if not celulas_valores or len(celulas_valores) <= indice_chutes: continue
                                
                                val_chute = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes]).strip()
                                
                                if val_chute in ["-", ""]:
                                    chutes = 0
                                else:
                                    match = re.search(r'\d+', val_chute)
                                    chutes = int(match.group()) if match else 0
                                
                                if chutes > 10: chutes = 0
                    
                                if nome_jogador not in stats["historico_chutes"]: stats["historico_chutes"][nome_jogador] = []
                                while len(stats["historico_chutes"][nome_jogador]) < jogo_global_index: stats["historico_chutes"][nome_jogador].append(0)
                                stats["historico_chutes"][nome_jogador].append(chutes)
                            except: continue
                    except Exception as e_passo2:
                        print(f" ⚠️ Erro ao carregar aba de finalizações: {e_passo2}")
                    
                    jogo_global_index += 1
                except: continue
    except Exception as e:
        print(f"      ⚠️ Erro na Raspagem 2: {e}")
            
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except: pass

return stats
