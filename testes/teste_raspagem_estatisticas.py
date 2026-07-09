#testes/teste_raspagem_estatisticas.py

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

    # Inicialização dos arrays para guardar o total de cantos de cada um dos últimos 3 jogos
    if "cantos_mandante_h2h" not in stats: stats["cantos_mandante_h2h"] = []
    if "cantos_visitante_h2h" not in stats: stats["cantos_visitante_h2h"] = []

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
                        elemento_alvo = linhas_confrontos[jogo_idx]
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

                    # 🎯 PASSO: Coleta de Escanteios na aba de Estatísticas do Confronto
                    url_stats_geral = f"{url_jogo_completa}/resumo/estatisticas-jogo/0"
                    driver.get(url_stats_geral)
                    time.sleep(2.0)

                    cantos_jogo_total = 0

                    try:
                        linhas_estatisticas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statisticsRow'], .stat__row")
                        for linha in linhas_estatisticas:
                            try:
                                categoria = linha.find_element(By.CSS_SELECTOR, "[class*='categoryName'], .stat__categoryName").text.strip().upper()
                                
                                if any(x in categoria for x in ["ESCANTEIOS", "CORNER KICKS", "CORNERS"]):
                                    val_casa = linha.find_element(By.CSS_SELECTOR, "[class*='homeValue'], .stat__homeValue").text.strip()
                                    val_fora = linha.find_element(By.CSS_SELECTOR, "[class*='awayValue'], .stat__awayValue").text.strip()
                                    
                                    cantos_casa = int(val_casa) if val_casa.isdigit() else 0
                                    cantos_fora = int(val_fora) if val_fora.isdigit() else 0
                                    
                                    cantos_jogo_total = cantos_casa + cantos_fora
                                    break  # Encontrou a linha de escanteios, pode parar o loop interno
                            except: continue
                    except Exception as e_passo_cantos:
                        print(f" ⚠️ Erro ao processar dados de escanteios: {e_passo_cantos}")

                    # Adiciona ao array correspondente do time atual do dia
                    if alvo["tipo"] == "MANDANTE":
                        stats["cantos_mandante_h2h"].append(cantos_jogo_total)
                    else:
                        stats["cantos_visitante_h2h"].append(cantos_jogo_total)

                except: continue
    except Exception as e:
        print(f"      ⚠️ Erro Crítico na Raspagem Coletiva Geral: {e}")

    # Garante simetria preenchendo com 0 caso algum jogo não tenha tido estatística coletada de cantos
    while len(stats["cantos_mandante_h2h"]) < 3: stats["cantos_mandante_h2h"].append(0)
    while len(stats["cantos_visitante_h2h"]) < 3: stats["cantos_visitante_h2h"].append(0)
            
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except: pass

    return stats
              
