import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_coletivas(driver, stats):
    """
    Navega no histórico H2H e extrai as estatísticas coletivas APENAS de cartões.
    Escanteios desativados sem quebrar a estrutura de dados esperada pelo robô.
    """
    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return stats

    # Inicialização dos arrays de estatísticas (mantidos para não quebrar outros módulos)
    if "cantos_mandante_h2h" not in stats: stats["cantos_mandante_h2h"] = []
    if "cantos_visitante_h2h" not in stats: stats["cantos_visitante_h2h"] = []
    if "cartoes_mandante_h2h" not in stats: stats["cartoes_mandante_h2h"] = []
    if "cartoes_visitante_h2h" not in stats: stats["cartoes_visitante_h2h"] = []
    
    # 🚫 Escanteios marcado como desativado/incompleto por padrão
    stats["dados_incompletos_cantos"] = True
    stats["dados_incompletos_cartoes"] = False

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
                        lista_urls_jogos.append({"idx": jogo_idx})
                    except Exception:
                        continue
            except Exception as e_coleta:
                print(f"      ⚠️ Erro ao listar linhas para estatísticas: {e_coleta}")
                continue

            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(url_h2h_base)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    
                    selector_linhas = f".h2h__section:nth-child({alvo['idx_secao']}) .h2h__row"
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                    if len(linhas_atualizadas) <= jogo_dados["idx"]:
                        continue
                    
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]

                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", elemento_alvo)
                    
                    try:
                        WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                    except Exception:
                        pass
                        
                    time.sleep(1.2)
                    url_jogo_completa = driver.current_url.split("?")[0].strip("/")

                    url_stats_geral = f"{url_jogo_completa}/resumo/estatisticas/total/"
                    driver.get(url_stats_geral)
                    time.sleep(1.2)

                    cantos_jogo_total = 0  # 🚫 Escanteios desativados (permanece 0)
                    cartoes_jogo_total = 0
                    
                    achou_cartoes = False

                    try:
                        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                        
                        # Verifica se a tabela de estatísticas existe na página
                        tem_tabela_stats = len(todos_spans) > 0

                        if not tem_tabela_stats:
                            # Tabela de estatísticas ausente no Flashscore
                            stats["dados_incompletos_cartoes"] = True
                            print(f"      ⚠️ Tabela de estatísticas ausente no Flashscore para este jogo.")
                        else:
                            for idx, span in enumerate(todos_spans):
                                texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                                
                                # 🚫 1. ESCANTEIOS DESATIVADOS
                                # if texto_elemento in ["ESCANTEIOS", "ESCANTEIO", "CORNER KICKS", "CORNERS"]: ...
                                
                                # 2. Captura de Cartões Amarelos (Mantido ativo)
                                if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                                    achou_cartoes = True
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        val_casa_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        val_fora_card = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        
                                        cartoes_casa = int(re.search(r'\d+', val_casa_card).group()) if re.search(r'\d+', val_casa_card) else 0
                                        cartoes_fora = int(re.search(r'\d+', val_fora_card).group()) if re.search(r'\d+', val_fora_card) else 0
                                        cartoes_jogo_total = cartoes_casa + cartoes_fora

                            # Validação individual apenas para cartões
                            if not achou_cartoes:
                                stats["dados_incompletos_cartoes"] = True

                        print(f"      📊 [DADOS COLETADOS] Cartões Amarelos: {cartoes_jogo_total}")
                    
                    except Exception as e_passo_stats:
                        print(f"      ⚠️ Erro ao processar dados de estatísticas via JS: {e_passo_stats}")
                        stats["dados_incompletos_cartoes"] = True

                    # Adiciona aos arrays mantendo compatibilidade
                    if alvo["tipo"] == "MANDANTE":
                        stats["cantos_mandante_h2h"].append(0)
                        stats["cartoes_mandante_h2h"].append(cartoes_jogo_total)
                    else:
                        stats["cantos_visitante_h2h"].append(0)
                        stats["cartoes_visitante_h2h"].append(cartoes_jogo_total)

                except Exception:
                    continue
    except Exception as e:
        print(f"      ⚠️ Erro Crítico na Raspagem Coletiva Geral: {e}")

    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass

    return stats
                            
