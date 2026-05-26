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
PATH_PENDENTES = os.path.join("ranking", "pendentes.json")

def log(etapa, message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 {etapa}: {message}")

def configuring_driver():
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
    os.makedirs(PATH_DIR, exist_ok=True)
    
    data_hoje_str = date.today().strftime("%Y-%m-%d")
    data_ontem_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    path_links_hoje = os.path.join(PATH_DIR, f"links_{data_hoje_str}.json")
    path_links_ontem = os.path.join(PATH_DIR, f"links_{data_ontem_str}.json")
    
    # =========================================================================
    # FASE 1: CAPTURA E VALIDAÇÃO DOS LINKS DE HOJE (PARA USAR AMANHÃ)
    # =========================================================================
    log("FASE 1", "Verificando o arquivo pendentes.json da madrugada atual...")
    
    if not os.path.exists(PATH_PENDENTES):
        log("AVISO", "O arquivo ranking/pendentes.json não existe. Falta os pendentes de hoje favor tentar amanhã.")
        return

    try:
        with open(PATH_PENDENTES, 'r', encoding='utf-8') as f:
            dados_pendentes = json.load(f)
            
        timestamp_mod = os.path.getmtime(PATH_PENDENTES)
        data_mod_pendentes = datetime.fromtimestamp(timestamp_mod).strftime("%Y-%m-%d")
        
        if data_mod_pendentes != data_hoje_str:
            log("AVISO", f"O pendentes.json encontrado é antigo ({data_mod_pendentes}). Falta os pendentes de hoje favor tentar amanhã.")
            return
            
    except Exception as e:
        log("ERRO", f"Não foi possível ler o arquivo pendentes.json: {e}")
        return

    # Salva a ponte de dados de hoje
    with open(path_links_hoje, 'w', encoding='utf-8') as f:
        json.dump(dados_pendentes, f, indent=4, ensure_ascii=False)
    log("SALVAMENTO", f"Links de hoje guardados com sucesso em: {path_links_hoje}")

    # =========================================================================
    # FASE 2: TRAVA DE SEGURANÇA E PROCESSAMENTO DOS RESULTADOS DE ONTEM
    # =========================================================================
    log("FASE 2", f"Verificando existência do arquivo de ontem: {path_links_ontem}")
    
    # 🛑 TRAVA SEGURO: Se o arquivo de ontem não existir, avisa e encerra imediatamente
    if not os.path.exists(path_links_ontem):
        log("TRAVA ATIVADA", f"Arquivo {path_links_ontem} não encontrado. Como este é o primeiro ciclo ou os links de ontem foram perdidos, a atualização da tabela de padrões começará automaticamente amanhã.")
        log("FIM", "Fase 1 concluída com sucesso. Fase 2 adiada para o próximo ciclo de amanhã.")
        return

    # --- CORREÇÃO DO BLOCO DE LEITURA NA FASE 2 ---
    with open(path_links_ontem, 'r', encoding='utf-8') as f:
        dados_json_ontem = json.load(f)

    # AJUSTE 1: Entra na chave "jogos" conforme a estrutura do seu print do repositório
    jogos_ontem = dados_json_ontem.get("jogos", [])

    if not jogos_ontem:
        log("AVISO", "O arquivo de links de ontem está vazio ou sem a chave 'jogos'. Encerrando execução.")
        return

    # Organiza em jogos únicos para não repetir requisições
    jogos_unicos = {}
    for p in jogos_ontem:
        # AJUSTE 2: Mapeia para 'link_h2h' (que é o padrão gerado pelo seu robô principal)
        url = p.get("link_h2h") or p.get("link_betano") or p.get("link")
        if not url:
            continue
        chave = f"{p['time_casa'].strip().lower()}x{p['time_fora'].strip().lower()}"
        if chave not in jogos_unicos:
            jogos_unicos[chave] = {
                "time_casa": p["time_casa"],
                "time_fora": p["time_fora"],
                "url": url
            }

    # Carrega ou inicia o banco histórico de padrões
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

    driver = configuring_driver()
    consolidados = 0

    try:
        for chave, jogo in jogos_unicos.items():
            log("SCRAPER", f"Conferindo placar de: {jogo['time_casa']} x {jogo['time_fora']}")
            try:
                driver.get(jogo["url"])
                wait = WebDriverWait(driver, 10)
                
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper, .event__score")))
                
                scores = driver.find_elements(By.CSS_SELECTOR, ".detailScore__wrapper span")
                if len(scores) >= 2:
                    score_casa = scores[0].text.strip()
                    score_fora = scores[2].text.strip()
                else:
                    score_casa = driver.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                    score_fora = driver.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()

                if score_casa.isdigit() and score_fora.isdigit():
                    g_c = int(score_casa)
                    g_f = int(score_fora)
                    
                    odd_casa, odd_fora = 2.50, 2.50

                    perfil = definir_perfil_jogo(odd_casa, odd_fora)
                    status_mercados = checar_mercados_ocorridos(g_c, g_f)
                    
                    db_padroes[data_ontem_str][perfil]["total_jogos"] += 1
                    for mercado, deu_green in status_mercados.items():
                        if deu_green:
                            db_padroes[data_ontem_str][perfil]["greens"][mercado] += 1
                            
                    consolidados += 1
                    log("CONSOLIDADO", f"Sucesso -> {jogo['time_casa']} ({g_c}x{g_f}) | Perfil: {perfil}")
                
                time.sleep(1.2)
                
            except Exception as e:
                log("ERRO JOGO", f"Não conseguiu ler o placar de {jogo['time_casa']}: {str(e)[:45]}")

        with open(PATH_PADROES_DB, 'w', encoding='utf-8') as f:
            json.dump(db_padroes, f, indent=4, ensure_ascii=False)
            
        log("SUCESSO", f"Varredura de ontem concluída! {consolidados} jogos integrados no padroes_db.json.")

    finally:
        driver.quit()

if __name__ == "__main__":
    processar_estatisticas()
    
