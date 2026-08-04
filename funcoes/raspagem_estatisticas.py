import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 🟢 LISTA BRANCA: Nomes-chave para busca flexível nas ligas de elite
LIGAS_ELITE_JOGADORES = [
    "brasileirão série a", "copa do brasil", "libertadores", "sul-americana",
    "brasileirão série b", "liga profesional", "argentina", "copa do mundo",
    "champions league", "premier league", "laliga", "bundesliga", "serie a", 
    "ligue 1", "europa league", "fa cup", "copa del rey", "dfb pokal", 
    "primeira liga", "eredivisie", "amistoso internacional"
]

def liga_eh_permitida(texto_liga):
    """
    Verifica se o nome da liga do confronto pertence à lista de ligas elite.
    """
    if not texto_liga:
        return False
    
    texto_clean = texto_liga.lower()
    return any(liga_elite in texto_clean for liga_elite in LIGAS_ELITE_JOGADORES)

def pegar_estatisticas_coletivas(driver, stats):
    """
    Navega no histórico H2H dos times e extrai EXCLUSIVAMENTE
    as estatísticas de FINALIZAÇÕES TOTAIS de jogos de LIGAS PERMITIDAS.
    """
    EXECUTAR_SCRAPER = True

    # Arrays para Finalizações
    stats["chutes_mandante_h2h"] = []   
    stats["chutes_visitante_h2h"] = []  
    stats["chutes_jogo_total_h2h"] = [] 
    stats["dados_incompletos_chutes"] = False

    if not EXECUTAR_SCRAPER:
        print("      ⏩ [SCRAPER DESATIVADO] Pulo da raspagem de estatísticas acionado.")
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return stats

    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return stats

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
                
                # Coleta até 5 jogos (padrão da esteira)
                for jogo_idx in range(min(5, len(linhas_confrontos))):
                    try:
                        lista_urls_jogos.append({"idx": jogo_idx})
                    except Exception:
                        continue
            except Exception as e_coleta:
                print(f"      ⚠️ Erro ao listar linhas H2H para estatísticas: {e_coleta}")
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

                    # 🔍 [NOVA VALIDAÇÃO DE LIGA] Leitura do nome da competição antes de clicar
                    try:
                        nome_liga_elemento = elemento_alvo.find_element(
                            By.CSS_SELECTOR, ".h2h__event, .h2h__competition, [class*='event'], [class*='competition']"
                        ).text.strip()
                    except Exception:
                        # Fallback: pega todo o texto da linha se não achar o seletor específico
                        nome_liga_elemento = elemento_alvo.text.strip()

                    if not liga_eh_permitida(nome_liga_elemento):
                        print(f"      ⏩ [LIGA DESCAR TADA]: '{nome_liga_elemento}' não está na lista branca. Pulando jogo...")
                        continue

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

                    chutes_casa = 0
                    chutes_fora = 0
                    achou_chutes = False

                    try:
                        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                        
                        if len(todos_spans) == 0:
                            print(f"      ⚠️ Tabela de estatísticas ausente no Flashscore.")
                        else:
                            achou_cartoes_ancora = False

                            for idx, span in enumerate(todos_spans):
                                texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                                
                                # Trava de segurança: se bateu na linha de cartões amarelados, interrompe
                                if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                                    achou_cartoes_ancora = True
                                
                                # Busca estrita do Total de Finalizações no topo (DESTAQUES)
                                if not achou_cartoes_ancora and texto_elemento in ["TOTAL DE FINALIZAÇÕES", "TOTAL SHOTS"]:
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        val_casa_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        val_fora_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        chutes_casa = int(re.search(r'\d+', val_casa_str).group()) if re.search(r'\d+', val_casa_str) else 0
                                        chutes_fora = int(re.search(r'\d+', val_fora_str).group()) if re.search(r'\d+', val_fora_str) else 0
                                        achou_chutes = True
                                        break # Pára a busca assim que pega a métrica do topo

                            if achou_chutes:
                                total_jogo = chutes_casa + chutes_fora
                                print(f"      📊 [{alvo['tipo']}] Finalizações Totais: Casa {chutes_casa} | Fora {chutes_fora} (Total: {total_jogo})")
                                
                                if alvo["tipo"] == "MANDANTE":
                                    stats["chutes_mandante_h2h"].append(chutes_casa)
                                else:
                                    stats["chutes_visitante_h2h"].append(chutes_fora)
                                    
                                stats["chutes_jogo_total_h2h"].append(total_jogo)
                            else:
                                print(f"      ⚠️ Total de finalizações não localizado no topo.")

                    except Exception as e_passo_stats:
                        print(f"      ⚠️ Erro ao capturar finalizações via JS: {e_passo_stats}")

                except Exception:
                    continue

    except Exception as e:
        print(f"      ⚠️ Erro Crítico na Raspagem de Estatísticas: {e}")

    # ----------------------------------------------------------
    # 🧮 CALCULA AS MÉDIAS DE FINALIZAÇÕES PARA O MAIN
    # ----------------------------------------------------------
    c_h2h = stats.get("chutes_mandante_h2h", [])
    v_h2h = stats.get("chutes_visitante_h2h", [])

    stats["mandante_media_chutes_casa"] = round(sum(c_h2h) / len(c_h2h), 2) if len(c_h2h) > 0 else 0.0
    stats["visitante_media_chutes_fora"] = round(sum(v_h2h) / len(v_h2h), 2) if len(v_h2h) > 0 else 0.0

    try:
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass

    return stats
                
