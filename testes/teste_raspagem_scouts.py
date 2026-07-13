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

    # 🟢 1. CAPTURA DE ELENCOS
    try:
        url_escalacoes = url_h2h_base.replace("/h2h/overall", "/escalacoes").replace("/h2h/total", "/escalacoes")
        print(f"         [RASPAGEM 3] Acessando Elencos: {url_escalacoes}")
        driver.get(url_escalacoes)
        time.sleep(2.5)
        
        jogadores_casa = driver.find_elements(By.CSS_SELECTOR, "[class*='home'] [class*='participantName'], .lf__side--home [class*='participantName']")
        for j in jogadores_casa:
            nome = driver.execute_script("return arguments[0].textContent;", j).strip()
            if nome and nome not in stats["elenco_mandante"]: stats["elenco_mandante"].append(nome)
            
        jogadores_fora = driver.find_elements(By.CSS_SELECTOR, "[class*='away'] [class*='participantName'], .lf__side--away [class*='participantName']")
        for j in jogadores_fora:
            nome = driver.execute_script("return arguments[0].textContent;", j).strip()
            if nome and nome not in stats["elenco_visitante"]: stats["elenco_visitante"].append(nome)
        print(f"         [RASPAGEM 3] Elencos Mapeados -> Mandante: {len(stats['elenco_mandante'])} | Visitante: {len(stats['elenco_visitante'])}")
    except Exception as e_elenco:
        print(f"         ⚠️ Erro ao mapear elencos: {e_elenco}")

    # 🟢 2. MAPEAMENTO DINÂMICO DE ESCUDOS E LINKS VIA H2H MÃE
    dicionario_escudos = {}
    links_jogos_historico = set()

    try:
        print(f"         [RASPAGEM 3] Acessando H2H Mãe para coletar confrontos e escudos: {url_h2h_base}")
        driver.get(url_h2h_base)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")))
        time.sleep(2.0)

        blocos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        
        # Varrer os blocos (Mandante e Visitante) capturando os primeiros 5 de cada
        for bloco in blocos_h2h[:2]:
            linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
            for linha_jogo in linhas_jogos[:5]:
                href = linha_jogo.get_attribute("href")
                if href:
                    links_jogos_historico.add(href)
                
                # Mapeia os escudos das linhas para o dicionário global
                participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
                for p in participantes:
                    try:
                        img_el = p.find_element(By.CSS_SELECTOR, "img")
                        src_img = img_el.get_attribute("src") or ""
                        nome_arquivo = src_img.split('/')[-1] if src_img else ""
                        nome_time = p.text.strip().upper()
                        if nome_arquivo and nome_time and nome_arquivo not in dicionario_escudos:
                            dicionario_escudos[nome_arquivo] = nome_time
                    except:
                        continue

        print(f"         [RASPAGEM 3] Mapeados {len(dicionario_escudos)} escudos via H2H.")
    except Exception as e_coleta:
        print(f"         🚨 Erro crítico ao listar linhas do H2H mãe: {e_coleta}")
        return stats

    lista_final_links = list(links_jogos_historico)[:10]
    print(f"         [RASPAGEM 3] Total de jogos históricos únicos para processar: {len(lista_final_links)}")

    # 🟢 3. PROCESSAMENTO DOS MERCADOS POR JOGO HISTÓRICO
    jogo_global_index = 0

    for url_jogo in lista_final_links:
        try:
            # Separa a URL base e o parâmetro mid de forma limpa
            if "?mid=" in url_jogo:
                parts = url_jogo.split("?mid=")
                url_base = parts[0].rstrip('/')
                mid_param = parts[1]
            else:
                url_base = url_jogo.split("/#")[0].rstrip('/')
                mid_param = ""

            # Executa a raspagem para os dois mercados usando a função unificada
            for mercado in ["finalizacoes", "ataque"]:
                url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}" if mid_param else f"{url_base}/resumo/estatisticas-jogadores/{mercado}/"
                driver.get(url_final)
                time.sleep(2.5) # Tempo estável de renderização da tabela

                # Define índices e termos dinâmicos
                if mercado == "finalizacoes":
                    termos_busca = ["ALVO", "TARGET", "NO GOL"]
                    indice_alvo_default = 5
                    chave_stats = "historico_chutes"
                else:
                    termos_busca = ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
                    indice_alvo_default = 4
                    chave_stats = "historico_faltas"

                # Identifica a coluna dinamicamente
                cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
                indice_alvo = -1
                for idx, th in enumerate(cabecalhos):
                    txt = th.text.strip().upper()
                    if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS", "FOULS"]):
                        indice_alvo = idx
                        break
                
                if indice_alvo == -1:
                    indice_alvo = indice_alvo_default

                linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
                
                for linha in linhas:
                    try:
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
                        
                        # Filtra apenas se o time pertencer ao confronto original analisado (t1 ou t2)
                        if not (t1.upper() in time_real.upper() or t2.upper() in time_real.upper()):
                            continue

                        celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                        if len(celulas) > indice_alvo:
                            valor_txt = celulas[indice_alvo].text.strip()
                            qtd_scout = int(re.search(r'\d+', valor_txt).group()) if re.search(r'\d+', valor_txt) else 0
                            
                            if nome_jogador not in stats[chave_stats]:
                                stats[chave_stats][nome_jogador] = []
                            
                            # Alinha o tamanho da lista com o index atual antes de inserir o valor
                            while len(stats[chave_stats][nome_jogador]) < jogo_global_index:
                                stats[chave_stats][nome_jogador].append(0)
                            
                            stats[chave_stats][nome_jogador].append(qtd_scout)
                    except:
                        continue

            # Incrementa o index apenas após rodar com sucesso os dois mercados do jogo atual
            jogo_global_index += 1
            print(f"         [RASPAGEM 3] Jogo [{jogo_global_index}/{len(lista_final_links)}] processado com sucesso.")

        except Exception as e_jogo:
            print(f"         ⚠️ Erro ao processar jogo histórico {url_jogo}: {e_jogo}")
            continue

    # 🟢 4. COMPATIBILIZAÇÃO FINAL DE ARRAYS (Garante que quem não jogou receba 0)
    for jogador, lista in stats["historico_chutes"].items():
        while len(lista) < jogo_global_index: lista.append(0)
    for jogador, lista in stats["historico_faltas"].items():
        while len(lista) < jogo_global_index: lista.append(0)

    print(f"         [RASPAGEM 3] Finalizada com sucesso. Total de jogos computados: {jogo_global_index}")
    return stats
