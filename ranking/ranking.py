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
PATH_DB = "ranking/ranking_db.json"
PATH_PENDENTES = "ranking/pendentes.json"

def log(etapa, mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 {etapa}: {mensagem}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
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

    # --- TRAVA DE SEGURANÇA: DATA DO ARQUIVO ---
    if not os.path.exists(PATH_PENDENTES):
        log("AVISO", "Arquivo pendentes.json não encontrado. Nada para processar.")
        return

    # Pega a data que o arquivo foi modificado
    data_modificacao = date.fromtimestamp(os.path.getmtime(PATH_PENDENTES))
    hoje = date.today()

    if data_modificacao >= hoje:
        log("TRAVA", f"O arquivo pendentes.json é de hoje ({data_modificacao}). O ranking só roda jogos de ONTEM.")
        log("DICA", "Aguarde até amanhã para validar os jogos que o main gerou hoje.")
        return

    # --- CARREGAMENTO DE DADOS ---
    with open(PATH_PENDENTES, 'r', encoding='utf-8') as f:
        pendentes = json.load(f)

    if not pendentes:
        log("AVISO", "A lista de pendentes está vazia.")
        return

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
                score_casa = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(1)"))).text
                score_fora = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(3)"))).text
                
                if score_casa.isdigit() and score_fora.isdigit():
                    g_c, g_f = int(score_casa), int(score_fora)
                    deu_green = validar_palpite(jogo['mercado'], g_c, g_f)
                    
                    m_rank = jogo['mercado_ranking']
                    if m_rank not in stats: stats[m_rank] = {"green": 0, "red": 0}
                    
                    if deu_green: stats[m_rank]['green'] += 1
                    else: stats[m_rank]['red'] += 1
                    
                    atualizados += 1
                    log("RESULTADO", f"{'✅ GREEN' if deu_green else '❌ RED'} ({g_c}-{g_f})")
                else:
                    log("PULANDO", "Jogo ainda não encerrado ou placar não disponível.")

            except Exception as e:
                log("ERRO", f"Não foi possível ler o jogo {jogo['time_casa']}: {e}")

        # --- SALVAMENTO E LIMPEZA ---
        db["stats"] = stats
        db["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        with open(PATH_DB, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        
        # Limpa o arquivo para não processar os mesmos jogos de novo
        with open(PATH_PENDENTES, 'w', encoding='utf-8') as f:
            json.dump([], f)
            
        log("FIM", f"Processo concluído. {atualizados} jogos contabilizados no Ranking DB.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
        
