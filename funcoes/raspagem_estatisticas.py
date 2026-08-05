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
    Navega nas abas específicas H2H de CASA (mandante) e FORA (visitante)
    utilizando a estrutura estável de cliques e extraindo EXCLUSIVAMENTE
    as estatísticas de FINALIZAÇÕES TOTAIS de jogos de LIGAS PERMITIDAS.
    """
    EXECUTAR_SCRAPER = True

    # Inicialização dos Arrays para Finalizações mantendo compatibilidade de chaves
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

    # Constrói as URLs segmentadas /h2h/casa/ e /h2h/fora/ a partir da url_h2h_base
    url_base_limpa = url_h2h_base.replace("/h2h", "").rstrip("/")
    url_casa = f"{url_base_limpa}/h2h/casa/"
    url_fora = f"{url_base_limpa}/h2h/fora/"

    configuracoes_alvo = [
        {"tipo": "MANDANTE", "url": url_casa, "chave_array": "chutes_mandante_h2h"},
        {"tipo": "VISITANTE", "url": url_fora, "chave_array": "chutes_visitante_h2h"}
    ]

    try:
        for alvo in configuracoes_alvo:
            lista_urls_jogos = []
            try:
                driver.get(alvo["url"])
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                
                # Na URL específica /h2h/casa/ ou /h2h/fora/, as linhas de interesse ficam na primeira seção
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section .h2h__row")
                
                # Coleta estritamente até 5 jogos do histórico
                for jogo_idx in range(min(5, len(linhas_confrontos))):
                    try:
                        lista_urls_jogos.append({"idx": jogo_idx})
                    except Exception:
                        continue
            except Exception as e_coleta:
                print(f"      ⚠️ Erro ao listar linhas H2H para chutes ({alvo['tipo']}): {e_coleta}")
                continue

            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(alvo["url"])
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, ".h2h__section .h2h__row")
                    if len(linhas_atualizadas) <= jogo_dados["idx"]:
                        continue
                    
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]

                    # 🔍 [VALIDAÇÃO DE LIGA] Leitura do nome da competição antes de clicar
                    try:
                        nome_liga_elemento = elemento_alvo.find_element(
                            By.CSS_SELECTOR, ".h2h__event, .h2h__competition, [class*='event'], [class*='competition']"
                        ).text.strip()
                    except Exception:
                        nome_liga_elemento = elemento_alvo.text.strip()

                    if not liga_eh_permitida(nome_liga_elemento):
                        print(f"      ⏩ [LIGA DESCARTADA]: '{nome_liga_elemento}' não está na lista branca. Pulando jogo...")
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
                                
                                if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                                    achou_cartoes_ancora = True
                                
                                if not achou_cartoes_ancora and texto_elemento in ["TOTAL DE FINALIZAÇÕES", "TOTAL SHOTS"]:
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        val_casa_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        val_fora_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        chutes_casa = int(re.search(r'\d+', val_casa_str).group()) if re.search(r'\d+', val_casa_str) else 0
                                        chutes_fora = int(re.search(r'\d+', val_fora_str).group()) if re.search(r'\d+', val_fora_str) else 0
                                        achou_chutes = True
                                        break 

                            if achou_chutes:
                                # Na aba de CASA do Mandante, o dado de interesse é o do mandante (casa).
                                # Na aba de FORA do Visitante, o dado de interesse é o do visitante (fora).
                                valor_alvo = chutes_casa if alvo["tipo"] == "MANDANTE" else chutes_fora
                                total_jogo = chutes_casa + chutes_fora
                                
                                print(f"      📊 [{alvo['tipo']}] Finalizações Capturadas: {valor_alvo} (Jogo Total: {total_jogo})")
                                stats[alvo["chave_array"]].append(valor_alvo)
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
                
