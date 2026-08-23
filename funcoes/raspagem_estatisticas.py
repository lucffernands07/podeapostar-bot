import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ligas import liga_eh_permitida

def formatar_rota_h2h(url_base, sub_rota=""):
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
    nome_comp = stats.get("liga", "")
    if not liga_eh_permitida(nome_comp):
        print(f"      ⏩ [RAIZ] Fase 2 ignorada: '{nome_comp}' não é liga de elite.")
        return stats

    EXECUTAR_SCRAPER = True

    # Chutes
    stats["chutes_mandante_h2h"] = []   
    stats["chutes_visitante_h2h"] = []  

    # Escanteios
    stats["cantos_mandante_h2h"] = []
    stats["cantos_visitante_h2h"] = []

    # Cartões
    stats["cartoes_mandante_h2h"] = []
    stats["cartoes_visitante_h2h"] = []
    stats["dados_incompletos_cartoes"] = False

    if not EXECUTAR_SCRAPER:
        return stats

    url_h2h_base = stats.get("url_h2h_base")
    if not url_h2h_base:
        print("      ⚠️ [LOG] url_h2h_base vazia nos stats.")
        return stats

    wait = WebDriverWait(driver, 10)

    try:
        if driver.current_url.rstrip("/") != url_h2h_base.rstrip("/"):
            driver.get(url_h2h_base)
            time.sleep(1.2)

        url_atual_carregada = driver.current_url.split('?')[0]
        url_base_limpa = url_atual_carregada.replace("/h2h", "").rstrip("/")

        rotas_alvo = [
            {"tipo": "MANDANTE", "url": formatar_rota_h2h(url_base_limpa, "casa"), "c_chutes": "chutes_mandante_h2h", "c_cantos": "cantos_mandante_h2h", "c_cartoes": "cartoes_mandante_h2h"},
            {"tipo": "VISITANTE", "url": formatar_rota_h2h(url_base_limpa, "fora"), "c_chutes": "chutes_visitante_h2h", "c_cantos": "cantos_visitante_h2h", "c_cartoes": "cartoes_visitante_h2h"}
        ]

        for alvo in rotas_alvo:
            print(f"      🔍 [LOG] Acessando URL {alvo['tipo']}: {alvo['url']}")
            try:
                driver.get(alvo["url"])
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")))
                time.sleep(0.8)
                
                linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
                links_jogos = []
                for linha in linhas_confrontos[:5]:
                    href = linha.get_attribute("href")
                    if not href:
                        try:
                            a_tag = linha.find_element(By.TAG_NAME, "a")
                            href = a_tag.get_attribute("href")
                        except Exception:
                            pass
                    if href:
                        links_jogos.append(href)

                for url_jogo in links_jogos:
                    url_jogo_base = url_jogo.split("?")[0].split("#")[0].strip("/")
                    url_stats_geral = f"{url_jogo_base}/resumo/estatisticas/total/"
                    
                    driver.get(url_stats_geral)
                    time.sleep(1.0)

                    chutes_casa, chutes_fora = 0, 0
                    cantos_casa, cantos_fora = 0, 0
                    cartoes_casa, cartoes_fora = 0, 0
                    
                    achou_chutes = False
                    achou_cantos = False
                    achou_cartoes = False

                    try:
                        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                        if len(todos_spans) > 0:
                            for idx, span in enumerate(todos_spans):
                                texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                                
                                # Chutes
                                if texto_elemento in ["TOTAL DE FINALIZAÇÕES", "TOTAL SHOTS"]:
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        c_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        f_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        chutes_casa = int(re.search(r'\d+', c_str).group()) if re.search(r'\d+', c_str) else 0
                                        chutes_fora = int(re.search(r'\d+', f_str).group()) if re.search(r'\d+', f_str) else 0
                                        achou_chutes = True

                                # Escanteios
                                if texto_elemento in ["ESCANTEIOS", "CORNERS"]:
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        c_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        f_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        cantos_casa = int(re.search(r'\d+', c_str).group()) if re.search(r'\d+', c_str) else 0
                                        cantos_fora = int(re.search(r'\d+', f_str).group()) if re.search(r'\d+', f_str) else 0
                                        achou_cantos = True

                                # Cartões Amarelos
                                if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                                    if idx > 0 and (idx + 1) < len(todos_spans):
                                        c_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                                        f_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                                        cartoes_casa = int(re.search(r'\d+', c_str).group()) if re.search(r'\d+', c_str) else 0
                                        cartoes_fora = int(re.search(r'\d+', f_str).group()) if re.search(r'\d+', f_str) else 0
                                        achou_cartoes = True

                            # Gravações condicionais por alvo
                            if achou_chutes:
                                stats[alvo["c_chutes"]].append(chutes_casa if alvo["tipo"] == "MANDANTE" else chutes_fora)
                            if achou_cantos:
                                stats[alvo["c_cantos"]].append(cantos_casa if alvo["tipo"] == "MANDANTE" else cantos_fora)
                            if achou_cartoes:
                                stats[alvo["c_cartoes"]].append(cartoes_casa if alvo["tipo"] == "MANDANTE" else cartoes_fora)

                    except Exception as e_sp:
                        print(f"      ⚠️ [LOG] Erro ao ler spans estatísticos: {e_sp}")

            except Exception as e_coleta:
                print(f"      ⚠️ [LOG] Erro ao listar linhas H2H: {e_coleta}")
                continue

    except Exception as e:
        print(f"      ⚠️ [LOG] Erro Crítico na Raspagem Coletiva: {e}")

    # Médias Finais
    c_h = stats.get("chutes_mandante_h2h", [])
    c_v = stats.get("chutes_visitante_h2h", [])
    stats["mandante_media_chutes_casa"] = round(sum(c_h) / len(c_h), 2) if len(c_h) > 0 else 0.0
    stats["visitante_media_chutes_fora"] = round(sum(c_v) / len(c_v), 2) if len(c_v) > 0 else 0.0

    return stats
    
