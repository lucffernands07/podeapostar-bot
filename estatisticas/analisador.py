import os
import sys
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

# --- CONFIGURAÇÕES DE CAMINHO ---
PATH_DIR = "estatisticas"
PATH_PADROES_DB = os.path.join(PATH_DIR, "padroes_db.json")
DIR_TELEGRAM = "telegram"

def log(etapa, mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 {etapa}: {mensagem}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def definir_perfil_jogo(odd_casa, odd_fora):
    try:
        o_c = float(str(odd_casa).replace(',', '.'))
        o_f = float(str(odd_fora).replace(',', '.'))
    except:
        return "EQUILIBRADO"

    if o_c <= 2.10:
        return "FAVORITO_CASA"
    elif o_f <= 2.10:
        return "FAVORITO_FORA"
    else:
        return "EQUILIBRADO"

def checar_mercados_ocorridos(g_c, g_f):
    total = g_c + g_f
    return {
        "1X": g_c >= g_f,
        "VITORIA_CASA": g_c > g_f,
        "2X": g_f >= g_c,
        "BTTS": g_c > 0 and g_f > 0,
        "+1.5": total >= 2,
        "+2.5": total >= 3,
        "-4.5": total <= 4
    }

def processar_estatisticas():
    # Calcula a data de ontem para buscar o arquivo correto (ex: se hoje é 26, busca o de dia 25)
    data_ontem_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    nome_arquivo_ontem = f"jogos_{data_ontem_str}.json"
    caminho_json_ontem = os.path.join(DIR_TELEGRAM, nome_arquivo_ontem)
    
    log("INÍCIO", f"Buscando arquivo de ontem: {caminho_json_ontem}")
    
    if not os.path.exists(caminho_json_ontem):
        log("ERRO", f"Arquivo {caminho_json_ontem} não foi encontrado para processamento.")
        return

    with open(caminho_json_ontem, 'r', encoding='utf-8') as f:
        dados_jogos = json.load(f)

    if not dados_jogos:
        log("AVISO", f"O arquivo {nome_arquivo_ontem} está vazio.")
        return

    # --- AGRUPAR POR JOGO UNICÓ ---
    jogos_unicos = {}
    for p in dados_jogos:
        url = p.get("link_betano") or p.get("link")
        if not url:
            continue
        chave = f"{p['time_casa'].strip().lower()}x{p['time_fora'].strip().lower()}"
        if chave not in jogos_unicos:
            jogos_unicos[chave] = {
                "time_casa": p["time_casa"],
                "time_fora": p["time_fora"],
                "url": url
            }

    # Iniciar ou carregar Banco Histórico de Padrões
    os.makedirs(PATH_DIR, exist_ok=True)
    if os.path.exists(PATH_PADROES_DB):
        with open(PATH_PADROES_DB, 'r', encoding='utf-8') as f:
            db_padroes = json.load(f)
    else:
        db_padroes = {}

    if data_ontem_str not in db_padroes:
        db_padroes[data_ontem_str] = {
            "FAVORITO_CASA": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}},
            "EQUILIBRADO": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}},
            "FAVORITO_FORA": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}}
        }

    driver = configurar_driver()
    consolidados = 0

    try:
        for chave, jogo in jogos_unicos.items():
            log("SCRAPER", f"Analisando: {jogo['time_casa']} x {jogo['time_fora']}")
            try:
                driver.get(jogo["url"])
                wait = WebDriverWait(driver, 15)
                
                # Captura do placar encerrado na Betano
                score_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".gcr-game-score, .score, .match-score")))
                
                if len(score_elements) >= 2:
                    g_c = int(score_elements[0].text.strip())
                    g_f = int(score_elements[1].text.strip())
                    
                    # Captura de odds pré-jogo no histórico da página
                    odds_elements = driver.find_elements(By.CSS_SELECTOR, ".odd, .gcr-odd-value")
                    
                    odd_casa, odd_fora = 2.50, 2.50 
                    if len(odds_elements) >= 3:
                        odd_casa = odds_elements[0].text.strip()
                        odd_fora = odds_elements[2].text.strip()

                    # Processamento de Regras Reversas
                    perfil = definir_perfil_jogo(odd_casa, odd_fora)
                    status_mercados = checar_mercados_ocorridos(g_c, g_f)
                    
                    db_padroes[data_ontem_str][perfil]["total_jogos"] += 1
                    for mercado, deu_green in status_mercados.items():
                        if deu_green:
                            db_padroes[data_ontem_str][perfil]["greens"][mercado] += 1
                            
                    consolidados += 1
                    log("CONSOLIDADO", f"Sucesso -> {jogo['time_casa']} ({g_c}x{g_f}) | Perfil: {perfil}")
            except Exception as e:
                log("ERRO JOGO", f"Falha ao extrair dados para {jogo['time_casa']}: {str(e)[:50]}")

        with open(PATH_PADROES_DB, 'w', encoding='utf-8') as f:
            json.dump(db_padroes, f, indent=4, ensure_ascii=False)
            
        log("SUCESSO", f"Mapeamento encerrado. {consolidados} jogos catalogados na data {data_ontem_str}!")

    finally:
        driver.quit()

if __name__ == "__main__":
    processar_estatisticas()
                  
