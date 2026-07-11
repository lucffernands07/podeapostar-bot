#testes/teste_raspagem_estatisticas.py
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_coletivas(driver, stats):
    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try: driver.switch_to.window(driver.window_handles[0])
        except: pass
        return stats

    # Inicialização dos arrays
    for chave in ["cantos_mandante_h2h", "cantos_visitante_h2h", "cartoes_mandante_h2h", "cartoes_visitante_h2h"]:
        if chave not in stats: stats[chave] = []

    wait = WebDriverWait(driver, 10)
    
    # ⚡ OTIMIZAÇÃO: Coleta as URLs diretamente sem cliques artificiais
    urls_por_tipo = {"MANDANTE": [], "VISITANTE": []}
    
    try:
        driver.get(url_h2h_base)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes_alvo = [
            {"tipo": "MANDANTE", "idx_secao": 1},
            {"tipo": "VISITANTE", "idx_secao": 2}
        ]
        
        for alvo in secoes_alvo:
            selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
            linhas = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
            
            for linha in linhas[:3]:
                try:
                    # Captura o ID/link diretamente mapeado no elemento clicável ou na linha
                    # Geralmente as linhas do Flashscore possuem o ID do jogo na classe ou atributo, 
                    # ou podemos obter simulando o clique em lote ou pegando a tag 'a' se houver.
                    # Caso a div não tenha link explícito, usamos uma abertura limpa e rápida:
                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", linha)
                    try: WebDriverWait(driver, 5).until(lambda d: d.current_url != url_anterior)
                    except: pass
                    
                    url_jogo = driver.current_url.split("?")[0].strip("/")
                    urls_por_tipo[alvo["tipo"]].append(url_jogo)
                    
                    # Volta imediatamente para pegar o próximo sem quebrar o estado
                    driver.get(url_h2h_base)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_linhas)))
                except:
                    continue
    except Exception as e_coleta:
        print(f"      ⚠️ Erro ao coletar URLs de estatísticas: {e_coleta}")

    # Processamento linear direto (Sem ir e voltar da Home H2H)
    for tipo, urls in urls_por_tipo.items():
        for url_jogo in urls:
            try:
                url_stats_geral = f"{url_jogo}/resumo/estatisticas/total/"
                driver.get(url_stats_geral)
                
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']"))
                    )
                except:
                    print(f"      ⏱️ [TIMEOUT] Estatísticas demoraram para aparecer na URL: {url_stats_geral}")
                    
                cantos_jogo_total = 0
                cartoes_jogo_total = 0

                todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                for idx, span in enumerate(todos_spans):
                    texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                    
                    if texto_elemento in ["ESCANTEIOS", "ESCANTEIO", "CORNER KICKS", "CORNERS"]:
                        if idx > 0 and (idx + 1) < len(todos_spans):
                            val_casa = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                            val_fora = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                            cantos_casa = int(re.search(r'\d+', val_casa).group()) if re.search(r'\d+', val_casa) else 0
                            cantos_fora = int(re.search(r'\d+', val_fora).group()) if re.search(r'\d+', val_fora) else 0
                            cantos_jogo_total = cantos_casa + cantos_fora
                            
                    elif texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                        if idx > 0 and (idx + 1) < len(todos_spans):
                            val_casa_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                            val_fora_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                            cartoes_casa = int(re.search(r'\d+', val_casa_card).group()) if re.search(r'\d+', val_casa_card) else 0
                            cartoes_fora = int(re.search(r'\d+', val_fora_card).group()) if re.search(r'\d+', val_fora_card) else 0
                            cartoes_jogo_total = cartoes_casa + cartoes_fora

                print(f"      📊 [DADOS COLETADOS] Tipo: {tipo} | Cantos: {cantos_jogo_total} | Cartões: {cartoes_jogo_total}")
                
                if tipo == "MANDANTE":
                    stats["cantos_mandante_h2h"].append(cantos_jogo_total)
                    stats["cartoes_mandante_h2h"].append(cartoes_jogo_total)
                else:
                    stats["cantos_visitante_h2h"].append(cantos_jogo_total)
                    stats["cartoes_visitante_h2h"].append(cartoes_jogo_total)
            except:
                continue

    # Garante simetria
    for chave in ["cantos_mandante_h2h", "cantos_visitante_h2h", "cartoes_mandante_h2h", "cartoes_visitante_h2h"]:
        while len(stats[chave]) < 3: stats[chave].append(0)

    try: driver.switch_to.window(driver.window_handles[0])
    except: pass
    return stats
