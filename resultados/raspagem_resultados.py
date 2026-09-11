import os
import time
import json
import re
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

PATH_DIR_JOGOS = "telegram"
PATH_DIR_RESULTADOS = "resultados"

def log(etapa, message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 {etapa}: {message}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extrair_dados_completos(driver, url_h2h):
    resultado_parcial = {
        "gols_casa": 0, "gols_fora": 0,
        "escanteios_casa": 0, "escanteios_fora": 0,
        "cartoes_casa": 0, "cartoes_fora": 0
    }
    
    try:
        # 1. Abre o link H2H apenas para obter a URL base limpa
        driver.get(url_h2h)
        time.sleep(2.5)
        url_atual = driver.current_url
        
        url_jogo_base = url_atual.split("?")[0].split("#")[0].strip("/")
        url_stats_geral = f"{url_jogo_base}/resumo/estatisticas/total/"
        
        log("URL ÚNICA", f"Acessando página de estatísticas: {url_stats_geral}")
        
        # 2. Vai direto para a aba de estatísticas
        driver.get(url_stats_geral)
        time.sleep(3.0)
        
        # 3. Captura o Placar (Gols)
        try:
            scores = driver.find_elements(By.CSS_SELECTOR, ".detailScore__wrapper span, [class*='detailScore'] span")
            if len(scores) >= 3:
                g_c = scores[0].text.strip()
                g_f = scores[2].text.strip()
                resultado_parcial["gols_casa"] = int(g_c) if g_c.isdigit() else 0
                resultado_parcial["gols_fora"] = int(g_f) if g_f.isdigit() else 0
            else:
                sc_home = driver.find_element(By.CSS_SELECTOR, ".matchScore__home, [class*='score--home']").text.strip()
                sc_away = driver.find_element(By.CSS_SELECTOR, ".matchScore__away, [class*='score--away']").text.strip()
                resultado_parcial["gols_casa"] = int(sc_home) if sc_home.isdigit() else 0
                resultado_parcial["gols_fora"] = int(sc_away) if sc_away.isdigit() else 0
        except Exception as e_gols:
            log("AVISO GOLS", f"Não foi possível capturar o placar: {e_gols}")

        # Função auxiliar interna para buscar valores baseados no título da estatística
        def buscar_stat_por_nome(nomes_alvo):
            try:
                spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
                for span in spans:
                    texto = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                    if any(n in texto for n in nomes_alvo):
                        # Sobe para o container pai da linha para isolar os valores daquele item específico
                        linha_pai = span.find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or ancestor::div[3]]")
                        valores = linha_pai.find_elements(By.CSS_SELECTOR, "[class*='wcl-value']")
                        
                        if len(valores) < 2:
                            # Fallback subindo mais um nível se necessário
                            linha_pai = span.find_element(By.XPATH, "./ancestor::div[2]")
                            valores = linha_pai.find_elements(By.CSS_SELECTOR, "[class*='wcl-value']")

                        if len(valores) >= 2:
                            m_c = re.search(r'\d+', valores[0].text)
                            m_f = re.search(r'\d+', valores[-1].text)
                            c_val = int(m_c.group()) if m_c else 0
                            f_val = int(m_f.group()) if m_f else 0
                            return c_val, f_val
            except Exception as e:
                log("AVISO BUSCA STAT", f"Erro ao buscar {nomes_alvo}: {e}")
            return 0, 0

        # 4. Captura Escanteios
        c_esc, f_esc = buscar_stat_por_nome(["ESCANTEIOS", "CORNERS"])
        resultado_parcial["escanteios_casa"] = c_esc
        resultado_parcial["escanteios_fora"] = f_esc

        # 5. Captura Cartões Amarelos
        c_cart, f_cart = buscar_stat_por_nome(["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"])
        resultado_parcial["cartoes_casa"] = c_cart
        resultado_parcial["cartoes_fora"] = f_cart

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
            dados_jogo = extrair_dados_completos(driver, url_h2h)
            
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
            
