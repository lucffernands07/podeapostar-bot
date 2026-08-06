import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LIGAS_ELITE_JOGADORES = [
    "brasileirão série a", "copa do brasil", "libertadores", "sul-americana",
    "brasileirão série b", "liga profesional", "argentina", "copa do mundo",
    "champions league", "premier league", "laliga", "bundesliga", "serie a", 
    "ligue 1", "europa league", "fa cup", "copa del rey", "dfb pokal", 
    "primeira liga", "eredivisie", "amistoso internacional"
]

def liga_eh_permitida(texto_liga):
    if not texto_liga:
        return False
    texto_clean = texto_liga.lower()
    return any(liga_elite in texto_clean for liga_elite in LIGAS_ELITE_JOGADORES)

def formatar_rota_h2h(url_base, sub_rota=""):
    """
    Formata a rota base já carregada pelo navegador para a sub-rota /casa/ ou /fora/.
    """
    path = url_base.split('?')[0].split('#')[0].rstrip('/')
    for sufixo in ['/overall', '/casa', '/fora']:
        if path.endswith(sufixo):
            path = path[:-len(sufixo)]

    if not path.endswith('/h2h'):
        path = f"{path}/h2h"

    if sub_rota:
        path = f"{path}/{sub_rota}"

    return f"{path}/"

def pegar_estatisticas_coletivas(driver, stats):
    EXECUTAR_SCRAPER = True

    stats["chutes_mandante_h2h"] = []   
    stats["chutes_visitante_h2h"] = []  
    stats["chutes_jogo_total_h2h"] = [] 
    stats["dados_incompletos_chutes"] = False

    if not EXECUTAR_SCRAPER:
        return stats

    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        print("      ⚠️ [LOG] url_h2h_base vazia nos stats.")
        return stats

    wait = WebDriverWait(driver, 10)

    try:
        # 1. Garante que a página base H2H já foi aberta/carregada pelo menos uma vez 
        # para o navegador resolver os slugs completos dos times a partir do ID
        if driver.current_url.rstrip("/") != url_h2h_base.rstrip("/"):
            driver.get(url_h2h_base)
            time.sleep(1.5)

        # 2. Pega a URL já expandida e carregada pelo navegador (com os nomes dos times)
        url_atual_carregada = driver.current_url.split('?')[0]
        url_base_limpa = url_atual_carregada.replace("/h2h", "").rstrip("/")

        rotas_alvo = [
            {"tipo": "MANDANTE", "url": formatar_rota_h2h(url_base_limpa, "casa"), "chave_array": "chutes_mandante_h2h"},
            {"tipo": "VISITANTE", "url": formatar_rota_h2h(url_base_limpa, "fora"), "chave_array": "chutes_visitante_h2h"}
        ]

        for alvo in rotas_alvo:
            print(f"      🔍 [LOG] Acessando URL {alvo['tipo']} (já carregada/expandida): {alvo['url']}")
            lista_urls_jogos = []
            try:
                driver.get(alvo["url"])
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")))
                time.sleep(1.0)
                
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")
                print(f"      📊 [LOG] Encontradas {len(linhas_confrontos)} linhas H2H para {alvo['tipo']}.")
                
                for jogo_idx in range(min(5, len(linhas_confrontos))):
                    lista_urls_jogos.append({"idx": jogo_idx})
            except Exception as e_coleta:
                print(f"      ⚠️ [LOG] Erro ao listar linhas H2H para chutes ({alvo['tipo']}): {e_coleta}")
                continue

            for jogo_dados in lista_urls_jogos:
                try:
                    driver.get(alvo["url"])
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")))
                    
                    linhas_atualizadas = driver.find_elements(By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")
                    if len(linhas_atualizadas) <= jogo_dados["idx"]:
                        continue
                    
                    elemento_alvo = linhas_atualizadas[jogo_dados["idx"]]

                    try:
                        nome_liga_elemento = elemento_alvo.find_element(
                            By.CSS_SELECTOR, ".h2h__event, .h2h__competition, [class*='event'], [class*='competition']"
                        ).text.strip()
                    except Exception:
                        nome_liga_elemento = elemento_alvo.text.strip()

                    if not liga_eh_permitida(nome_liga_elemento):
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
                        if len(todos_spans) > 0:
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
                                valor_alvo = chutes_casa if alvo["tipo"] == "MANDANTE" else chutes_fora
                                stats[alvo["chave_array"]].append(valor_alvo)
                    except Exception:
                        pass

                except Exception:
                    continue

    except Exception as e:
        print(f"      ⚠️ [LOG] Erro Crítico na Raspagem Coletiva de Chutes: {e}")

    c_h2h = stats.get("chutes_mandante_h2h", [])
    v_h2h = stats.get("chutes_visitante_h2h", [])

    stats["mandante_media_chutes_casa"] = round(sum(c_h2h) / len(c_h2h), 2) if len(c_h2h) > 0 else 0.0
    stats["visitante_media_chutes_fora"] = round(sum(v_h2h) / len(v_h2h), 2) if len(v_h2h) > 0 else 0.0

    print(f"      📊 [LOG FINAL] Médias -> Mandante Casa: {stats['mandante_media_chutes_casa']} | Visitante Fora: {stats['visitante_media_chutes_fora']}")

    try:
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass

    return stats
                                        
