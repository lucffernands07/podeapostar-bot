import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_coletivas(driver, stats):
    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except: pass
        return stats

    # Inicialização dos arrays para Escanteios (H2H)
    if "cantos_mandante_h2h" not in stats: stats["cantos_mandante_h2h"] = []
    if "cantos_visitante_h2h" not in stats: stats["cantos_visitante_h2h"] = []
    
    # 🚨 NOVO: Inicialização dos arrays para Cartões Amarelos (H2H)
    if "cartoes_mandante_h2h" not in stats: stats["cartoes_mandante_h2h"] = []
    if "cartoes_visitante_h2h" not in stats: stats["cartoes_visitante_h2h"] = []

    wait = WebDriverWait(driver, 10)

    secoes_alvo_stats = [
        {"tipo": "MANDANTE", "idx_secao": 1},
        {"tipo": "VISITANTE", "idx_secao": 2}
    ]

    try:
        for alvo in secoes_alvo_stats:
            lista_urls_jogos = []
            try:
                driver.get(url_h2h_base)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                
                for jogo_idx in range(min(3, len(linhas_confrontos))):
                    try:
                        lista_urls_jogos.append({
                            "idx": jogo_idx
                        })
                    except: continue
            except Exception as e_coleta:
                print(f"      ⚠️ Erro ao listar linhas para estatísticas: {e_coleta}")
                continue

            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(url_h2h_base)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    
                    selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                    if len(linhas_atualizadas) <= jogo_dados["idx"]: continue
                    
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]

                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", elemento_alvo)
                    
                    try: WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                    except: pass
                        
                    time.sleep(2.5)
                    url_jogo_completa = driver.current_url.split("?")[0].strip("/")

                    url_stats_geral = f"{url_jogo_completa}/resumo/estatisticas/total/"
                    driver.get(url_stats_geral)
                    time.sleep(2.0)

                    cantos_jogo_total = 0
                    cartoes_jogo_total = 0

                    try:
                        # Pega todos os spans com a classe unificada de texto da tabela
                        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                        
                        for idx, span in enumerate(todos_spans):
                            texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                            
                            # 1. Captura de Escanteios
                            if texto_elemento in ["ESCANTEIOS", "ESCANTEIO", "CORNER KICKS", "CORNERS"]:
                                if idx > 0 and (idx + 1) < len(todos_spans):
                                    val_casa = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                    val_fora = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                    
                                    cantos_casa = int(re.search(r'\d+', val_casa).group()) if re.search(r'\d+', val_casa) else 0
                                    cantos_fora = int(re.search(r'\d+', val_fora).group()) if re.search(r'\d+', val_fora) else 0
                                    cantos_jogo_total = cantos_casa + cantos_fora
                            
                            # 2. 🚨 NOVO: Captura de Cartões Amarelos
                            elif texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                                if idx > 0 and (idx + 1) < len(todos_spans):
                                    val_casa_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                    val_fora_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                    
                                    cartoes_casa = int(re.search(r'\d+', val_casa_card).group()) if re.search(r'\d+', val_casa_card) else 0
                                    cartoes_fora = int(re.search(r'\d+', val_fora_card).group()) if re.search(r'\d+', val_fora_card) else 0
                                    cartoes_jogo_total = cartoes_casa + cartoes_fora

                        print(f"      📊 [DADOS COLETADOS] Cantos: {cantos_jogo_total} | Cartões Amarelos: {cartoes_jogo_total}")
                    
                    except Exception as e_passo_stats:
                        print(f"      ⚠️ Erro ao processar dados de estatísticas via JS: {e_passo_stats}")

                    # Adiciona aos arrays correspondentes do time alvo
                    if alvo["tipo"] == "MANDANTE":
                        stats["cantos_mandante_h2h"].append(cantos_jogo_total)
                        stats["cartoes_mandante_h2h"].append(cartoes_jogo_total)
                    else:
                        stats["cantos_visitante_h2h"].append(cantos_jogo_total)
                        stats["cartoes_visitante_h2h"].append(cartoes_jogo_total)

                except: continue
    except Exception as e:
        print(f"      ⚠️ Erro Crítico na Raspagem Coletiva Geral: {e}")

    # Garante simetria para escanteios e cartões preenchendo com 0 se faltar algum jogo
    while len(stats["cantos_mandante_h2h"]) < 3: stats["cantos_mandante_h2h"].append(0)
    while len(stats["cantos_visitante_h2h"]) < 3: stats["cantos_visitante_h2h"].append(0)
    while len(stats["cartoes_mandante_h2h"]) < 3: stats["cartoes_mandante_h2h"].append(0)
    while len(stats["cartoes_visitante_h2h"]) < 3: stats["cartoes_visitante_h2h"].append(0)
            
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except: pass

    return stats
                    
