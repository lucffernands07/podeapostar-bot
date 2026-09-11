import os
import time
import json
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PATH_DIR_JOGOS = "app/src/main/assets/jogos"
PATH_DIR_RESULTADOS = os.path.join("estatisticas")

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

def extrair_estatisticas_partida(driver, url_h2h):
    resultado_parcial = {
        "gols_casa": 0, "gols_fora": 0,
        "escanteios_casa": 0, "escanteios_fora": 0,
        "cartoes_casa": 0, "cartoes_fora": 0
    }
    
    try:
        driver.get(url_h2h)
        time.sleep(3) # Aguarda o redirecionamento automático do Flashscore para o jogo específico
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
                
            resultado_parcial["gols_casa"] = int(g_c)
            resultado_parcial["gols_fora"] = int(g_f)
        except Exception as e:
            log("AVISO GOLS", f"Não foi possível extrair o placar exato: {e}")

        # 2. Montagem e Acesso à URL de Estatísticas Detalhadas (/resumo/estatisticas/total/)
        if "?mid=" in url_atual:
            partes = url_atual.split("?mid=")
            base_url = partes[0].rstrip("/")
            mid_param = partes[1]
            
            url_estatisticas = f"{base_url}/resumo/estatisticas/total/?mid={mid_param}"
            
            driver.get(url_estatisticas)
            time.sleep(2.5)
            
            linhas = driver.find_elements(By.CSS_SELECTOR, ".statistics__row, .stat__row")
            for linha in linhas:
                texto_linha = linha.text.lower()
                if "escanteios" in texto_linha or "corner" in texto_linha:
                    valores = linha.find_elements(By.CSS_SELECTOR, ".statistics__value, .stat__homeValue, .stat__awayValue")
                    if len(valores) >= 2:
                        resultado_parcial["escanteios_casa"] = int(valores[0].text.strip() or 0)
                        resultado_parcial["escanteios_fora"] = int(valores[1].text.strip() or 0)
                
                elif "cartões" in texto_linha or "cards" in texto_linha or "amarelos" in texto_linha:
                    valores = linha.find_elements(By.CSS_SELECTOR, ".statistics__value, .stat__homeValue, .stat__awayValue")
                    if len(valores) >= 2:
                        resultado_parcial["cartoes_casa"] = int(valores[0].text.strip() or 0)
                        resultado_parcial["cartoes_fora"] = int(valores[1].text.strip() or 0)

    except Exception as e:
        log("ERRO PARTIDA", f"Falha ao processar link: {e}")
        
    return resultado_parcial

def processar_resultados_ontem():
    os.makedirs(PATH_DIR_RESULTADOS, exist_ok=True)
    
    data_ontem_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    path_arquivo_ontem = os.path.join(PATH_DIR_JOGOS, f"jogos_{data_ontem_str}.json")
    path_salvar_resultados = os.path.join(PATH_DIR_RESULTADOS, f"resultados_{data_ontem_str}.json")
    
    if not os.path.exists(path_arquivo_ontem):
        log("AVISO", f"Nenhum arquivo de jogos encontrado para ontem ({data_ontem_str}).")
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
            
            # Salva o JSON limpo sem odd e sem status
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
            
        log("SUCESSO", f"Resultados limpos salvos em: {path_salvar_resultados}")

    finally:
        driver.quit()

if __name__ == "__main__":
    processar_resultados_ontem()
      
