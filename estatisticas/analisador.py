import os
import sys
import time
import json
import argparse
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES DE CAMINHO NA NOVA PASTA ---
PATH_DIR = "estatisticas"
PATH_TEMP_ODDS = os.path.join(PATH_DIR, "odds_temporarias.json")
PATH_PADROES_DB = os.path.join(PATH_DIR, "padroes_db.json")

# Dicionário de Competições herdado do seu projeto principal
COMPETICOES = {
    "Brasileirão Série A": "https://www.flashscore.com.br/futebol/brasil/brasileirao-betano/jogos/",
    "Brasileirão Série B": "https://www.flashscore.com.br/futebol/brasil/serie-b/jogos/",
    "Brasileirão Série C": "https://www.flashscore.com.br/futebol/brasil/serie-c/jogos/",
    "Argentina - Liga Profesional": "https://www.flashscore.com.br/futebol/argentina/liga-profesional/jogos/",
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/jogos/",
    "Premier League": "https://www.flashscore.com.br/futebol/inglaterra/premier-league/jogos/",
    "LaLiga": "https://www.flashscore.com.br/futebol/espanha/laliga/jogos/",
    "Bundesliga": "https://www.flashscore.com.br/futebol/alemanha/bundesliga/jogos/",
    "Serie A (Itália)": "https://www.flashscore.com.br/futebol/italia/serie-a/jogos/",
    "Ligue 1": "https://www.flashscore.com.br/futebol/franca/ligue-1/jogos/",
    "Alemanha - 2. Bundesliga": "https://www.flashscore.com.br/futebol/alemanha/2-bundesliga/jogos/",
    "Argentina Primera B": "https://www.flashscore.com.br/futebol/argentina/primera-b/jogos/",
    "Armênia Premier League": "https://www.flashscore.com.br/futebol/armenia/premier-league/jogos/"
}

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

# ==========================================
# 🕒 TURNO 08:00 AM - CAPTURAR ODDS DE HOJE
# ==========================================
def turno_capturar_odds():
    log("INÍCIO", "Iniciando Turno das 08:00 - Captura de Odds Iniciais")
    os.makedirs(PATH_DIR, exist_ok=True)
    
    driver = configurar_driver()
    hoje_str = date.today().strftime("%Y-%m-%d")
    
    jogos_mapeados = {}

    try:
        for nome_liga, url in COMPETICOES.items():
            log("SCRAPER", f"Acessando liga: {nome_liga}")
            try:
                driver.get(url)
                time.sleep(3) # Aguarda renderização básica dos cards
                
                # Coleta as linhas dos jogos agendados/em andamento
                linhas_jogos = driver.find_elements(By.CSS_SELECTOR, ".sportName .event__match")
                
                for linha in linhas_jogos:
                    try:
                        id_jogo = linha.get_attribute("id").split("_")[-1]
                        link_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
                        
                        time_casa = linha.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                        time_fora = linha.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()
                        
                        # Captura as 3 colunas de odds fixas expostas na listagem principal (.event__odd)
                        odds_elements = linha.find_elements(By.CSS_SELECTOR, ".event__odd")
                        if len(odds_elements) >= 3:
                            odd_casa = odds_elements[0].text.strip()
                            odd_fora = odds_elements[2].text.strip()
                            
                            if odd_casa and odd_fora and odd_casa != "-" and odd_fora != "-":
                                chave_jogo = f"{time_casa.lower()}x{time_fora.lower()}".strip()
                                jogos_mapeados[chave_jogo] = {
                                    "time_casa": time_casa,
                                    "time_fora": time_fora,
                                    "odd_casa": odd_casa,
                                    "odd_fora": odd_fora,
                                    "link_h2h": link_h2h
                                }
                    except Exception as e:
                        continue
            except Exception as e:
                log("ERRO LIGA", f"Falha ao processar liga {nome_liga}: {str(e)[:50]}")

        # Salva o arquivo temporário de trabalho
        dados_salvamento = {"data": hoje_str, "jogos": jogos_mapeados}
        with open(PATH_TEMP_ODDS, 'w', encoding='utf-8') as f:
            json.dump(dados_salvamento, f, indent=4, ensure_ascii=False)
            
        log("SUCESSO", f"Mapeamento concluído. {len(jogos_mapeados)} jogos guardados para amanhã.")

    finally:
        driver.quit()

# ==========================================
# 🕒 TURNO 05:00 AM - PROCESSAR RESULTADOS
# ==========================================
def turno_processar_resultados():
    log("INÍCIO", "Iniciando Turno das 05:00 - Processamento Engenharia Reversa")
    
    if not os.path.exists(PATH_TEMP_ODDS):
        log("ERRO", "Arquivo temporário de odds não encontrado. Execute o turno das 08:00 primeiro.")
        return

    with open(PATH_TEMP_ODDS, 'r', encoding='utf-8') as f:
        dados_temporarios = json.load(f)

    data_jogos = dados_temporarios.get("data", "")
    jogos_salvos = dados_temporarios.get("jogos", {})

    if not jogos_salvos:
        log("AVISO", "Nenhum jogo salvo na lista temporária para analisar.")
        return

    # Carrega ou inicializa o banco consolidado histórico de padrões
    if os.path.exists(PATH_PADROES_DB):
        with open(PATH_PADROES_DB, 'r', encoding='utf-8') as f:
            db_padroes = json.load(f)
    else:
        db_padroes = {}

    if data_jogos not in db_padroes:
        db_padroes[data_jogos] = {
            "FAVORITO_CASA": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}},
            "EQUILIBRADO": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}},
            "FAVORITO_FORA": {"total_jogos": 0, "greens": {"1X": 0, "VITORIA_CASA": 0, "2X": 0, "BTTS": 0, "+1.5": 0, "+2.5": 0, "-4.5": 0}}
        }

    driver = configurar_driver()
    consolidados = 0

    try:
        for chave, jogo in jogos_salvos.items():
            url = jogo.get("link_h2h")
            log("VALIDANDO", f"Buscando resultado de: {jogo['time_casa']} x {jogo['time_fora']}")
            
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 12)
                
                # Seletor idêntico ao do seu ranking.py para ler os placares encerrados
                score_casa_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(1)")))
                score_fora_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(3)")))
                
                score_casa = score_casa_el.text.strip()
                score_fora = score_fora_el.text.strip()
                
                if score_casa.isdigit() and score_fora.isdigit():
                    g_c, g_f = int(score_casa), int(score_fora)
                    
                    # Decide a prateleira com base nas odds coletadas às 08:00 do dia anterior
                    perfil = definir_perfil_jogo(jogo["odd_casa"], jogo["odd_fora"])
                    status_mercados = checar_mercados_ocorridos(g_c, g_f)
                    
                    # Contabiliza no banco
                    db_padroes[data_jogos][perfil]["total_jogos"] += 1
                    for mercado, deu_green in status_mercados.items():
                        if deu_green:
                            db_padroes[data_jogos][perfil]["greens"][mercado] += 1
                            
                    consolidados += 1
                    log("CONSOLIDADO", f"Perfil: {perfil} | Placar: {g_c}-{g_f}")
            except Exception as e:
                log("ERRO JOGO", f"Não foi possível extrair placar para {jogo['time_casa']}: {str(e)[:50]}")

        # Grava as métricas consolidadas de volta no banco de dados
        with open(PATH_PADROES_DB, 'w', encoding='utf-8') as f:
            json.dump(db_padroes, f, indent=4, ensure_ascii=False)

        # Remove o arquivo de odds temporárias de trabalho após concluir o processamento com sucesso
        if os.path.exists(PATH_TEMP_ODDS):
            os.remove(PATH_TEMP_ODDS)
            
        log("FIM", f"Processamento finalizado. {consolidados} partidas injetadas no histórico de padrões!")

    finally:
        driver.quit()

# --- CONTROLADOR CENTRAL DE ARGUMENTOS ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robô de Engenharia Reversa - Padrões de Greens")
    parser.add_argument("--capturar", action="store_true", help="Executa o bloco das 08:00 para guardar as odds de hoje")
    parser.add_argument("--processar", action="store_true", help="Executa o bloco das 05:00 para processar placares e somar greens")
    
    args = parser.parse_args()
    
    if args.capturar:
        turno_capturar_odds()
    elif args.processar:
        turno_processar_resultados()
    else:
        print("⚠️ Use um argumento válido: python estatisticas/analisador.py --capturar OU --processar")
