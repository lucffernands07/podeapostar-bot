import os
import time
import json
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES DE CAMINHO ---
PATH_DB = "ranking_db.json"
PATH_PENDENTES = "ranking/pendentes.json"

def log(etapa, mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 {etapa}: {mensagem}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def validar_palpite(mercado_str, g_c, g_f):
    m = mercado_str.lower()
    total = g_c + g_f
    if "+1.5" in m: return total >= 2
    if "+2.5" in m: return total >= 3
    if "-4.5" in m: return total <= 4
    if "ambas marcam" in m or "btts" in m: return g_c > 0 and g_f > 0
    if "1x" in m: return g_c >= g_f
    if "x2" in m: return g_f >= g_c
    if "vitoria casa" in m: return g_c > g_f
    return False

def main():
    log("INÍCIO", "Iniciando Processamento de Ranking")

    if not os.path.exists(PATH_PENDENTES):
        log("AVISO", "Arquivo pendentes.json não encontrado. Nada para processar.")
        return

    # --- CARREGAMENTO DE DADOS E VALIDAÇÃO DE DATA ---
    with open(PATH_PENDENTES, 'r', encoding='utf-8') as f:
        dados_pendentes = json.load(f)

    # Suporte ao novo formato (dicionário) ou antigo (lista direta)
    if isinstance(dados_pendentes, dict):
        data_geracao = dados_pendentes.get("data_geracao", "")
        pendentes = dados_pendentes.get("jogos", [])
    else:
        data_geracao = "antigo"
        pendentes = dados_pendentes

    hoje_str = date.today().strftime("%Y-%m-%d")

    # TRAVA: Só processa se a data gravada no arquivo for anterior a hoje
    if data_geracao == hoje_str:
        log("TRAVA", f"O arquivo pendentes.json já é de hoje ({data_geracao}).")
        log("DICA", "O ranking só processa jogos de ONTEM. Aguarde o próximo ciclo.")
        return

    if not pendentes:
        log("AVISO", "A lista de jogos pendentes está vazia.")
        return

    # --- CARREGAMENTO DO BANCO DE DADOS ---
    if os.path.exists(PATH_DB):
        with open(PATH_DB, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"stats": {}}

    stats = db.get("stats", {})
    driver = configurar_driver()
    atualizados = 0

    try:
        for jogo in pendentes:
            url = jogo.get("link_h2h")
            if not url: continue

            log("PROCESSO", f"Validando: {jogo['time_casa']} x {jogo['time_fora']}")
            
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 15)
                
                # Busca o placar no topo da página de resumo
                score_casa_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(1)")))
                score_fora_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(3)")))
                
                score_casa = score_casa_el.text.strip()
                score_fora = score_fora_el.text.strip()
                
                if score_casa.isdigit() and score_fora.isdigit():
                    g_c, g_f = int(score_casa), int(score_fora)
                    deu_green = validar_palpite(jogo['mercado'], g_c, g_f)
                    
                    # --- PADRONIZAÇÃO DA CHAVE (REMOVE ESPAÇOS E DEIXA TUDO IGUAL) ---
                    m_rank = jogo['mercado_ranking'].strip().upper()
                    
                    if m_rank not in stats: 
                        stats[m_rank] = {"green": 0, "red": 0}
                    
                    if deu_green: 
                        stats[m_rank]['green'] += 1
                    else: 
                        stats[m_rank]['red'] += 1
                    
                    atualizados += 1
                    log("RESULTADO", f"{'✅ GREEN' if deu_green else '❌ RED'} ({g_c}-{g_f})")

                else:
                    log("PULANDO", f"Placar inválido ou jogo em andamento: {score_casa}-{score_fora}")

            except Exception as e:
                log("ERRO", f"Erro ao ler {jogo['time_casa']}: {str(e)[:50]}...")

        # --- SALVAMENTO E RESET DO ARQUIVO ---
        db["stats"] = stats
        db["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        with open(PATH_DB, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        
        # Limpa mantendo a data de hoje para manter a trava ativa
        dados_reset = {
            "data_geracao": hoje_str,
            "jogos": []
        }
        with open(PATH_PENDENTES, 'w', encoding='utf-8') as f:
            json.dump(dados_reset, f, indent=4, ensure_ascii=False)
            
        log("FIM", f"Processo concluído. {atualizados} jogos contabilizados.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                    
