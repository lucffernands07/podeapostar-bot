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

    if not url_h2h_base:
        print("         🚨 [RASPAGEM 3] Abortando: URL inválida!")
        return stats

    if "historico_chutes" not in stats: stats["historico_chutes"] = {}
    if "historico_faltas" not in stats: stats["historico_faltas"] = {}

    wait = WebDriverWait(driver, 15)
    dicionario_escudos = {}
    links_jogos_historico = set()

    # 🟢 1. MAPEAMENTO DE ESCUDOS E LINKS VIA H2H MÃE
    try:
        driver.get(url_h2h_base)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")))
        
        blocos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        for bloco in blocos_h2h[:2]:
            linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
            for linha_jogo in linhas_jogos[:5]:
                href = linha_jogo.get_attribute("href")
                if href: links_jogos_historico.add(href)
                
                participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
                for p in participantes:
                    try:
                        img_el = p.find_element(By.CSS_SELECTOR, "img")
                        src_img = img_el.get_attribute("src") or ""
                        nome_arquivo = src_img.split('/')[-1] if src_img else ""
                        nome_time = p.text.strip().upper()
                        if nome_arquivo and nome_time: dicionario_escudos[nome_arquivo] = nome_time
                    except: continue
        print(f"         [RASPAGEM 3] Mapeados {len(dicionario_escudos)} escudos.")
    except Exception as e:
        print(f"         🚨 Erro ao listar H2H: {e}")
        return stats

    lista_final_links = list(links_jogos_historico)[:10]
    jogo_global_index = 0

    # 🟢 2. PROCESSAMENTO DOS MERCADOS
    for url_jogo in lista_final_links:
        try:
            mid_param = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
            url_base = url_jogo.split("?mid=")[0].rstrip('/')

            for mercado in ["finalizacoes", "ataque"]:
                url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
                driver.get(url_final)
                
                # Aguarda a tabela renderizar
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")))
                except:
                    continue

                termos_busca = ["ALVO", "TARGET", "NO GOL"] if mercado == "finalizacoes" else ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
                chave_stats = "historico_chutes" if mercado == "finalizacoes" else "historico_faltas"
                indice_alvo = 5 if mercado == "finalizacoes" else 4

                linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], .wcl-table__row_, [data-testid='wcl-tableRow']")
                
                for linha in linhas:
                    try:
                        celula_jogador = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
                        nome_jogador = celula_jogador.text.strip()
                        if not nome_jogador or "TODOS" in nome_jogador: continue
                        
                        img_logo = linha.find_element(By.CSS_SELECTOR, "img")
                        arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                        time_real = dicionario_escudos.get(arquivo_linha, "")
                        
                        # DEBUG: Se não encontrar jogador, descomente a linha abaixo
                        # print(f"DEBUG: Comparando {t1}/{t2} com {time_real}")
                        
                        if not any(t.upper() in time_real.upper() for t in [t1, t2]): continue

                        celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                        valor_txt = celulas[indice_alvo].text.strip()
                        qtd = int(re.search(r'\d+', valor_txt).group()) if re.search(r'\d+', valor_txt) else 0
                        
                        if nome_jogador not in stats[chave_stats]: stats[chave_stats][nome_jogador] = []
                        while len(stats[chave_stats][nome_jogador]) < jogo_global_index: stats[chave_stats][nome_jogador].append(0)
                        stats[chave_stats][nome_jogador].append(qtd)
                    except: continue

            jogo_global_index += 1
            print(f"         [RASPAGEM 3] Jogo [{jogo_global_index}/{len(lista_final_links)}] ok.")
            time.sleep(1.5) # Respiro para o Flashscore não bloquear
        except Exception as e_jogo:
            print(f"         ⚠️ Erro no jogo histórico: {e_jogo}")
            continue

    # 🟢 3. COMPATIBILIZAÇÃO
    for jogador, lista in stats["historico_chutes"].items():
        while len(lista) < jogo_global_index: lista.append(0)
    for jogador, lista in stats["historico_faltas"].items():
        while len(lista) < jogo_global_index: lista.append(0)

    return stats
            
