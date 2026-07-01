import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_scouts_avancados(driver, stats, t1, t2):
    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except: pass
        return stats

    # Garante que todas as chaves necessárias existam no retorno
    if "historico_chutes" not in stats: stats["historico_chutes"] = {}
    if "historico_faltas" not in stats: stats["historico_faltas"] = {}
    if "elenco_mandante" not in stats: stats["elenco_mandante"] = []
    if "elenco_visitante" not in stats: stats["elenco_visitante"] = []

    wait = WebDriverWait(driver, 10)

    # 🟢 CAPTURA OS ELENCOS DIRETO NA ABA DE ESCALAÇÕES DO CONFRONTO ATUAL
    try:
        url_escalacoes = driver.current_url.replace("/h2h/overall", "/escalacoes")
        if "/escalacoes" in url_escalacoes:
            driver.get(url_escalacoes)
            time.sleep(2.5)
            
            # Pega todos os nomes de jogadores que pertencem ao bloco da esquerda (Mandante)
            jogadores_casa = driver.find_elements(By.CSS_SELECTOR, ".lf__side--home .lf__participantName, [class*='home'] [class*='participantName']")
            for j in jogadores_casa:
                nome = driver.execute_script("return arguments[0].textContent;", j).strip()
                if nome: stats["elenco_mandante"].append(nome)
                
            # Pega todos os nomes de jogadores que pertencem ao bloco da direita (Visitante)
            jogadores_fora = driver.find_elements(By.CSS_SELECTOR, ".lf__side--away .lf__participantName, [class*='away'] [class*='participantName']")
            for j in jogadores_fora:
                nome = driver.execute_script("return arguments[0].textContent;", j).strip()
                if nome: stats["elenco_visitante"].append(nome)
    except Exception as e_elenco:
        print(f"      ⚠️ Não foi possível mapear elencos da partida: {e_elenco}")

    # Retorna para o fluxo normal do H2H para pegar o histórico anterior
    try:
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

                    # Captura os hashes dos logos do jogo (Mandante/Visitante deste jogo histórico)
                    hash_mandante_topo, hash_visitante_topo = "", ""
                    try:
                        img_m = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image")
                        hash_mandante_topo = img_m.get_attribute("src").split('/')[-1]
                        img_v = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image")
                        hash_visitante_topo = img_v.get_attribute("src").split('/')[-1]
                    except: pass

                    # 🎯 PASSO 2: Coleta de Chutes
                    url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
                    driver.get(url_finalizacoes)
                    
                    try:
                        driver.execute_script("window.scrollTo(0, 300);")
                        time.sleep(1.5)
                        
                        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .fp-playerName_E6lgN")) > 0)
                        
                        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
                        indice_chutes = 5  
                        for idx_th, th in enumerate(cabecalhos_fin):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            if any(x in texto_th for x in ["ALVO", "FN", "SHOTS", "SOT"]):
                                indice_chutes = idx_th
                                break
                    
                        linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                        for lambda_linha in linhas_dados_fin:
                            try:
                                try:
                                    nome_element = lambda_linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName'], [data-testid='wcl-playerCell']")
                                except: continue
                                    
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                                if not nome_jogador or nome_jogador == "TODOS": continue
                                
                                try:
                                    img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='wcl-teamLogo'] img")
                                    hash_linha = img_linha.get_attribute("src").split('/')[-1]
                                    
                                    time_identificado = ""
                                    if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                                    elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                                    else: continue 
                                    
                                    if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                                        continue
                                except: continue

                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                                if len(celulas_valores) <= indice_chutes: continue
                                
                                val_chute = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes]).strip()
                                chutes = int(re.search(r'\d+', val_chute).group()) if re.search(r'\d+', val_chute) else 0
                    
                                if nome_jogador not in stats["historico_chutes"]: stats["historico_chutes"][nome_jogador] = []
                                while len(stats["historico_chutes"][nome_jogador]) < jogo_global_index: stats["historico_chutes"][nome_jogador].append(0)
                                stats["historico_chutes"][nome_jogador].append(chutes)
                            except: continue
                    except Exception as e_passo2:
                        print(f" ⚠️ Erro ao processar dados de finalizações nesta partida: {e_passo2}")

                    # 🎯 PASSO 3: Coleta de Faltas Sofridas
                    url_ataque = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
                    driver.get(url_ataque)
                    
                    try:
                        driver.execute_script("window.scrollTo(0, 300);")
                        time.sleep(1.5)
                        
                        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], [class*='playerName']")) > 0)
                        
                        cabecalhos_atq = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
                        indice_faltas = 5  
                        for idx_th, th in enumerate(cabecalhos_atq):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            if any(x in texto_th for x in ["SOFRIDAS", "FALTAS SOFRIDAS", "FOULS SUFFERED", "FS"]):
                                indice_faltas = idx_th
                                break
                    
                        linhas_dados_atq = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                        for lambda_linha in linhas_dados_atq:
                            try:
                                try:
                                    nome_element = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], .fp-playerName_E6lgN")
                                except: continue
                                    
                                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                                if not nome_jogador or nome_jogador == "TODOS": continue
                                
                                try:
                                    img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='wcl-teamLogo'] img")
                                    hash_linha = img_linha.get_attribute("src").split('/')[-1]
                                    
                                    time_identificado = ""
                                    if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                                    elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                                    else: continue 
                                    
                                    if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                                        continue
                                except: continue

                                celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                                if len(celulas_valores) <= indice_faltas: continue
                                
                                val_falta = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_faltas]).strip()
                                faltas_sof = int(re.search(r'\d+', val_falta).group()) if re.search(r'\d+', val_falta) else 0
                    
                                if nome_jogador not in stats["historico_faltas"]: stats["historico_faltas"][nome_jogador] = []
                                while len(stats["historico_faltas"][nome_jogador]) < jogo_global_index: stats["historico_faltas"][nome_jogador].append(0)
                                stats["historico_faltas"][nome_jogador].append(faltas_sof)
                            except: continue
                    except Exception as e_passo3:
                        print(f" ⚠️ Erro ao processar dados de faltas sofridas nesta partida: {e_passo3}")

                    jogo_global_index += 1
                except: continue
    except Exception as e:
        print(f"      ⚠️ Erro na Raspagem: {e}")
            
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except: pass

    return stats
                 
