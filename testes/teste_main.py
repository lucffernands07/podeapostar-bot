import os
import time
import re
import requests
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importação dos seus módulos
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes 
import odds  
import bingo357  
import links
from telegram import menus

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver


def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    """
    RASPAGEM 1: Abre a aba, acessa o H2H, captura o link Betano, gols, placares e resultados.
    MANTÉM A ABA ABERTA para o main avaliar se vale a pena continuar para os scouts avançados.
    """
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_45_under": 0, "fora_btts": 0, 
        "fora_vitorias_recente": 0, "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", 
        "h2h_geral_res_1": "", "h2h_geral_res_2": "", "h2h_geral_res_3": "", "h2h_geral_res_4": "", "h2h_geral_res_5": "",
        "t1_placar_1": None, "t2_placar_1": None,     
        "h2h_placar_1": None, "h2h_placar_2": None,   
        "pular_gols": False,
        "url_h2h_base": None,
        # Inicializados vazios por segurança caso o jogo não passe nos filtros iniciais
        "historico_chutes": {}, 
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {}
    }
    
    # Abre o confronto em uma nova aba
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # Clica na aba H2H do Flashscore
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(2)
        
        # Guarda a URL base do H2H para a Raspagem 2 usar se for necessário
        stats["url_h2h_base"] = driver.current_url

        # --- CAPTURA DO LINK DA BETANO ---
        try:
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            # Presume que o seu módulo 'links' importado cuida dessa extração
            import links 
            stats["link_betano"] = links.extrair_url_betano(driver)
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano inicial: {e_link}")
        
        # Rola a página para carregar as seções de jogos anteriores
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")

        # Varre as 3 seções clássicas: Últimos jogos Mandante, Últimos jogos Visitante e Confrontos Diretos
        for idx, secao in enumerate(secoes[:3]): 
            if idx == 2: 
                # Tenta expandir para ver mais confrontos diretos se o botão existir
                try:
                    seletor_btn = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao.find_element(By.CSS_SELECTOR, seletor_btn)
                    driver.execute_script("arguments[0].click();", botao_mais)
                    WebDriverWait(secao, 6).until(lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6)
                except: 
                    pass 

            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            for i, linha in enumerate(linhas):
                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                    
                    # Salva placares textuais recentes para o relatório
                    if idx == 0 and i == 0: stats["t1_placar_1"] = res_texto
                    if idx == 1 and i == 0: stats["t2_placar_1"] = res_texto
                    if idx == 2:
                        if i == 0: stats["h2h_placar_1"] = res_texto
                        if i == 1: stats["h2h_placar_2"] = res_texto

                    # Extrai os gols numéricos do placar
                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: 
                        continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    total = g1 + g2

                    # Seções 0 (Mandante) e 1 (Visitante)
                    if idx < 2: 
                        prefixo = "casa" if idx == 0 else "fora"
                        t_ref = t1 if idx == 0 else t2
                        
                        if i == 0: stats[f"ultimo_gols_{prefixo}"] = total
                        if total > 1.5: stats[f"{prefixo}_15"] += 1
                        if total > 2.5: stats[f"{prefixo}_25"] += 1
                        if total <= 4: stats[f"{prefixo}_45_under"] += 1 
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1
                        
                        res_atual = "E"
                        if (t_ref.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t_ref.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_atual = "V"
                            stats[f"{prefixo}_vitorias_recente"] += 1
                        elif (t_ref.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t_ref.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_atual = "D"
                        
                        if i == 0: stats[f"t{idx+1}_resultado_1"] = res_atual
                 
                    # Seção 2 (Confronto Direto H2H Histórico)
                    elif idx == 2: 
                        if i < 5:
                            res_geral = "EMPATE"
                            if g1 > g2:
                                if t1.lower() in n_casa_h2h.lower(): res_geral = "CASA"
                                elif t2.lower() in n_casa_h2h.lower(): res_geral = "FORA"
                            elif g1 < g2:
                                if t1.lower() in n_fora_h2h.lower(): res_geral = "CASA"
                                elif t2.lower() in n_fora_h2h.lower(): res_geral = "FORA"
                            
                            stats[f"h2h_geral_res_{i+1}"] = res_geral

                        # Garante a perspectiva fixa do Mandante nos confrontos diretos
                        if t1.lower() in n_fora_h2h.lower():
                            continue 

                        stats["h2h_jogos"] += 1
                        res_h2h = "E"
                        if g1 > g2:
                            res_h2h = "V"
                            stats["h2h_vitorias_t1"] += 1
                        elif g1 < g2:
                            res_h2h = "D"
                            stats["h2h_vitorias_t2"] += 1
                        
                        if stats["h2h_res_1"] == "":
                            stats["h2h_res_1"] = res_h2h
                        elif stats["h2h_res_2"] == "":
                            stats["h2h_res_2"] = res_h2h

                        if g1 == g2: stats["h2h_empates"] += 1
                except: 
                    continue
    except Exception as e:
        print(f"      ⚠️ Erro na Raspagem 1: {e}")
        
    return stats

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

                    
