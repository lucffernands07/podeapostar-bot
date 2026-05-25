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
    # Calcula a data de ontem para buscar o arquivo JSON correto
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

    # --- AGRUPAR POR JOGO ÚNICO ---
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
                "url": url,
                "odd_palpite": p.get("odd", "2.50")  # Salva a odd do palpite caso precise
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
                wait = WebDriverWait(driver, 12)
                
                # --- SELETORES ATUALIZADOS DA BETANO PARA EVENTO ENCERRADO ---
                # 1. Tenta encontrar pelo novo padrão de score-container ou classes alternativas
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='score-container'], .sc-fbNXWD, .match-score")))
                    score_casa_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='home-team-score'], .score-home")
                    score_fora_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='away-team-score'], .score-away")
                    score_casa = score_casa_el.text.strip()
                    score_fora = score_fora_el.text.strip()
                except:
                    # Seletor alternativo caso a página mude muito rápido
                    scores = driver.find_elements(By.CSS_SELECTOR, ".gcr-game-score, .score")
                    if len(scores) >= 2:
                        score_casa, score_fora = scores[0].text.strip(), scores[1].text.strip()
                    else:
                        raise Exception("Placar não localizado na página.")

                if score_casa.isdigit() and score_fora.isdigit():
                    g_c = int(score_casa)
                    g_f = int(score_fora)
                    
                    # --- CAPTURA DE ODDS PRÉ-JOGO DA BETANO ---
                    odd_casa, odd_fora = 2.50, 2.50  # Valor padrão equilibrado caso as odds sumam após o término
                    try:
                        odds_botoes = driver.find_elements(By.CSS_SELECTOR, "[data-testid='odd-button'] .odd-value, .gcr-odd-value")
                        if len(odds_botoes) >= 3:
                            odd_casa = odds_botoes[0].text.strip()
                            odd_fora = odds_botoes[2].text.strip()
                    except:
                        pass

                    # Processamento de Regras Reversas
                    perfil = definir_perfil_jogo(odd_casa, odd_fora)
                    status_mercados = checar_mercados_ocorridos(g_c, g_f)
                    
                    db_padroes[data_ontem_str][perfil]["total_jogos"] += 1
                    for mercado, deu_green in status_mercados.items():
                        if deu_green:
                            db_padroes[data_ontem_str][perfil]["greens"][mercado] += 1
                            
                    consolidados += 1
                    log("CONSOLIDADO", f"Sucesso -> {jogo['time_casa']} ({g_c}x{g_f}) | Perfil: {perfil}")
                
                time.sleep(1.5) # Delay de segurança
                
            except Exception as e:
                log("ERRO JOGO", f"Falha ao extrair dados para {jogo['time_casa']}: {str(e)[:45]}")

        with open(PATH_PADROES_DB, 'w', encoding='utf-8') as f:
            json.dump(db_padroes, f, indent=4, ensure_ascii=False)
            
        log("SUCESSO", f"Mapeamento encerrado. {consolidados} jogos catalogados com sucesso!")

    finally:
        driver.quit()

if __name__ == "__main__":
    processar_estatisticas()
            
