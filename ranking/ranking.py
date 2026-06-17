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
PATH_RANKING_DIARIO = "ranking/ranking_diario.json" 

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
    
    # 🚀 NOVO: Se for mercado de jogador, não valida pelo placar de gols (retorna None)
    if "chutes" in m or "faltas" in m or "média" in m:
        return None
        
    total = g_c + g_f
    if "+1.5" in m: return total >= 2
    if "+2.5" in m: return total >= 3
    if "-4.5" in m: return total <= 4
    if "ambas marcam" in m or "btts" in m: return g_c > 0 and g_f > 0
    if "1x" in m: return g_c >= g_f
    if "x2" in m: return g_f >= g_c
    if "vitoria casa" in m: return g_c > g_f
    return False

# --- FUNÇÃO CORRIGIDA: GERA O ARQUIVO PLANO FOCADO APENAS EM MERCADOS ---
def gerar_ranking_diario(stats_mercados):
    log("RANKING", "Gerando novo ranking_diario.json plano ordenado por assertividade...")
    
    ranking_final = []
    
    # Monta e ordena a lista de Mercados Simples diretamente na lista principal
    for mercado, dados in stats_mercados.items():
        g = dados.get('green', 0)
        r = dados.get('red', 0)
        total = g + r
        if total > 0:
            ranking_final.append({
                "mercado": mercado,
                "green": g,
                "red": r,
                "assertividade": g / total
            })
            
    # Ordena pelo maior aproveitamento (e usa o número de greens como critério de desempate)
    ranking_final.sort(key=lambda x: (x['assertividade'], x['green']), reverse=True)
    
    # Grava como uma lista pura, exatamente como o seu sender.py espera ler
    with open(PATH_RANKING_DIARIO, 'w', encoding='utf-8') as f:
        json.dump(ranking_final, f, indent=4, ensure_ascii=False)
        
    log("RANKING", "Arquivo ranking_diario.json gravado com sucesso em formato de lista plano.")

def main():
    log("INÍCIO", "Iniciando Processamento de Ranking")

    if not os.path.exists(PATH_PENDENTES):
        log("AVISO", "Arquivo pendentes.json não encontrado. Nada para processar.")
        return

    with open(PATH_PENDENTES, 'r', encoding='utf-8') as f:
        dados_pendentes = json.load(f)

    if isinstance(dados_pendentes, dict):
        data_geracao = dados_pendentes.get("data_geracao", "")
        pendentes = dados_pendentes.get("jogos", [])
    else:
        data_geracao = "antigo"
        pendentes = dados_pendentes

    # --- TRAVA CORRIGIDA: Só bloqueia o processamento se a lista estiver vazia ---
    if not pendentes:
        log("TRAVA", "A lista de jogos pendentes está vazia. O dia já foi processado.")
        return

    hoje_str = date.today().strftime("%Y-%m-%d")

    # Garante o carregamento correto das chaves do banco de dados relacional
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
                
                score_casa_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(1)")))
                score_fora_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".detailScore__wrapper span:nth-child(3)")))
                
                score_casa = score_casa_el.text.strip()
                score_fora = score_fora_el.text.strip()
                
                if score_casa.isdigit() and score_fora.isdigit():
                    g_c, g_f = int(score_casa), int(score_fora)
                    
                    deu_green = validar_palpite(jogo['mercado'], g_c, g_f)
                    
                    # 🚀 NOVO: Se o retorno for None, significa mercado de jogador. Pula a gravação no banco.
                    if deu_green is None:
                        log("IGNORADO", f"Mercado de Jogador detectado ({jogo['mercado']}). Pulando auditoria automatizada.")
                        continue
                    
                    m_rank = jogo['mercado_ranking'].strip().upper()
                    
                    # 🛠️ --- PADRONIZAÇÃO EXCLUSIVA DE ESCRITA ---
                    m_rank = m_rank.replace("VITÓRIA", "VITORIA")
                    m_rank = m_rank.replace("2X", "X2")
                    # --------------------------------------------
                    
                    if m_rank not in stats: 
                        stats[m_rank] = {"green": 0, "red": 0}
                    
                    if deu_green: 
                        stats[m_rank]['green'] += 1
                    else: 
                        stats[m_rank]['red'] += 1
                    
                    atualizados += 1
                    log("RESULTADO", f"{'✅ GREEN' if deu_green else '❌ RED'} ({g_c}-{g_f})")

            except Exception as e:
                log("ERRO", f"Erro ao ler {jogo['time_casa']}: {str(e)[:50]}...")

        # --- SALVAMENTO FINAL NO BANCO DE DADOS (APENAS MERCADOS) ---
        db["stats"] = stats
        db["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Limpa restos de chaves antigas de bingos do banco, se existirem
        if "stats_bingos" in db:
            del db["stats_bingos"]
        
        with open(PATH_DB, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        
        # GERA O NOVO RANKING DIÁRIO PLANO
        gerar_ranking_diario(stats)
            
        log("FIM", f"Processo concluído. {atualizados} mercados contabilizados com sucesso.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
