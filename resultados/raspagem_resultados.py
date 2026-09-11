import os
import time
import json
import re
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PATH_DIR_JOGOS = "telegram"
PATH_DIR_RESULTADOS = "resultados"

def log(etapa, message):
    print(f"[{datetime.now().strftime('%H:%M:%S']}] 📊 {etapa}: {message}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extrair_estatisticas_partida(driver, url_h2h):
    resultado_parcial = {
        "gols_casa": 0, "gols_fora": 0,
        "escanteios_casa": 0, "escanteios_fora": 0,
        "cartoes_casa": 0, "cartoes_fora": 0
    }
    
    try:
        driver.get(url_h2h)
        time.sleep(3)
        url_atual = driver.current_url
        
        # 1. Extração de Gols (Placar)
        try:
            scores = driver.find_elements(By.CSS_SELECTOR, ".detailScore__wrapper span")
            if len(scores) >= 3:
                g_c = scores[0].text.strip()
                g_f = scores[2].text.strip()
            else:
                g_c = driver.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                g_f = driver.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()
                
            resultado_parcial["gols_casa"] = int(g_c) if g_c.isdigit() else 0
            resultado_parcial["gols_fora"] = int(g_f) if g_f.isdigit() else 0
        except Exception as e:
            log("AVISO GOLS", f"Não foi possível extrair o placar exato: {e}")

        # 2. Acesso à URL de estatísticas utilizando a lógica padrão do bot
        url_jogo_base = url_atual.split("?")[0].split("#")[0].strip("/")
        url_stats_geral = f"{url_jogo_base}/resumo/estatisticas/total/"
        
        log("URL STATS", f"Acessando estatísticas: {url_stats_geral}")
        
        driver.get(url_stats_geral)
        time.sleep(2.0)
        
        try:
            todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
            if len(todos_spans) > 0:
                for idx, span in enumerate(todos_spans):
                    texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                    
                    # Escanteios (mesma lógica do bot)
                    if texto_elemento in ["ESCANTEIOS", "CORNERS"]:
                        if idx > 0 and (idx + 1) < len(todos_spans):
                            c_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                            f_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                            match_c = re.search(r'\d+', c_str)
                            match_f = re.search(r'\d+', f_str)
                            resultado_parcial["escanteios_casa"] = int(match_c.group()) if match_c else 0
                            resultado_parcial["escanteios_fora"] = int(match_f.group()) if match_f else 0

                    # Cartões Amarelos (mesma lógica do bot)
                    if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                        if idx > 0 and (idx + 1) < len(todos_spans):
                            c_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                            f_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                            match_c = re.search(r'\d+', c_str)
                            match_f = re.search(r'\d+', f_str)
                            resultado_parcial["cartoes_casa"] = int(match_c.group()) if match_c else 0
                            resultado_parcial["cartoes_fora"] = int(match_f.group()) if match_f else 0

        except Exception as e_sp:
            log("AVISO STATS", f"Erro ao ler spans estatísticos: {e_sp}")

    except Exception as e:
        log("ERRO PARTIDA", f"Falha ao processar link: {e}")
        
    return resultado_parcial

def processar_resultados_ontem():
    os.makedirs(PATH_DIR_RESULTADOS, exist_ok=True)
    
    data_ontem_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    path_arquivo_ontem = os.path.join(PATH_DIR_JOGOS, f"jogos_{data_ontem_str}.json")
    path_salvar_resultados = os.path.join(PATH_DIR_RESULTADOS, f"resultados_{data_ontem_str}.json")
    
    if not os.path.exists(path_arquivo_ontem):
        log("AVISO", f"Nenhum arquivo de jogos encontrado na pasta telegram para ontem ({data_ontem_str}).")
        return

    with open(path_arquivo_ontem, 'r', encoding='utf-8') as f:
        jogos_ontem = json.load(f)

    driver = configurar_driver()
    lista_resultados = []

    try:
        for jogo in jogos_ontem:
            url_h2h = jogo.get("link_h2h")
            if not url_h2h:
                continue
                
            log("SCRAPER", f"Raspando: {jogo['time_casa']} x {jogo['time_fora']}")
            dados_jogo = extrair_estatisticas_partida(driver, url_h2h)
            
            lista_resultados.append({
                "horario": jogo.get("horario"),
                "liga": jogo.get("liga"),
                "time_casa": jogo.get("time_casa"),
                "time_fora": jogo.get("time_fora"),
                "mercado": jogo.get("mercado"),
                "gols_casa": dados_jogo["gols_casa"],
                "gols_fora": dados_jogo["gols_fora"],
                "escanteios_casa": dados_jogo["escanteios_casa"],
                "escanteios_fora": dados_jogo["escanteios_fora"],
                "cartoes_casa": dados_jogo["cartoes_casa"],
                "cartoes_fora": dados_jogo["cartoes_fora"]
            })
            time.sleep(1)

        with open(path_salvar_resultados, 'w', encoding='utf-8') as f:
            json.dump(lista_resultados, f, indent=4, ensure_ascii=False)
            
        log("SUCESSO", f"Resultados salvos com sucesso em: {path_salvar_resultados}")

    finally:
        driver.quit()

if __name__ == "__main__":
    processar_resultados_ontem()
                        
