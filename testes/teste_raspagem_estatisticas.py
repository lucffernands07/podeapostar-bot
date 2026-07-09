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

                    # 🎯 Sua URL que abre exatamente a tela do print:
                    url_stats_geral = f"{url_jogo_completa}/resumo/estatisticas/total/"
                    driver.get(url_stats_geral)
                    time.sleep(2.5) # Garante o carregamento dos Destaques na tela

                    cantos_jogo_total = 0

                    # 🚨 NOVO MÉTODO DE EXTRAÇÃO BASEADO NO SEU PRINT E HTML VALIDADO
                    try:
                        # 1. Localiza diretamente o span com o texto "Escanteios"
                        elemento_categoria = driver.find_element(
                            By.XPATH, 
                            "//span[@data-testid='wcl-scores-simple-text-01' and (text()='Escanteios' or text()='Escanteio' or text()='Corner Kicks' or text()='Corners')]"
                        )
                        
                        # 2. Sobe para a div pai que engloba a linha inteira da estatística
                        linha_estatistica = elemento_categoria.find_element(By.XPATH, "./..")
                        
                        # 3. Pega todos os spans que usam o mesmo data-testid dentro dessa linha
                        valores = linha_estatistica.find_elements(By.XPATH, ".//span[@data-testid='wcl-scores-simple-text-01']")
                        
                        # Estrutura esperada: [Span_Valor_Casa, Span_Texto_Escanteios, Span_Valor_Fora]
                        if len(valores) >= 3:
                            val_casa = valores[0].text.strip()
                            val_fora = valores[2].text.strip()
                            
                            cantos_casa = int(val_casa) if val_casa.isdigit() else 0
                            cantos_fora = int(val_fora) if val_fora.isdigit() else 0
                            
                            cantos_jogo_total = cantos_casa + cantos_fora
                            print(f"      📊 [Estatísticas] Cantos coletados: {cantos_casa} (Casa) + {cantos_fora} (Fora) = Total: {cantos_jogo_total}")
                    
                    except Exception as e_passo_cantos:
                        print(f"      ⚠️ Não encontrou a linha de Escanteios nessa URL do jogo.")

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
            
