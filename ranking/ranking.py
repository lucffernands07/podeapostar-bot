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
PATH_BINGOS_DO_DIA = "ranking/bingos_do_dia.json"  # <--- Arquivo gerado pelo bingo357.py

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

# --- NOVA FUNÇÃO: CONFERE OS BINGOS DA MADRUGADA ANTERIOR ---
def conferir_bingos_do_dia(resultados_jogos, stats_bingos):
    log("BINGOS", "Iniciando conferência dos Bingos do dia anterior (Regra Tudo ou Nada)...")
    
    if not os.path.exists(PATH_BINGOS_DO_DIA):
        log("AVISO BINGOS", "Arquivo bingos_do_dia.json não encontrado para checagem.")
        return stats_bingos

    try:
        with open(PATH_BINGOS_DO_DIA, 'r', encoding='utf-8') as f:
            bingos_salvos = json.load(f)
            
        for nome_bingo, jogos_do_bingo in bingos_salvos.items():
            if not jogos_do_bingo: continue
            
            # Inicializa a estrutura no banco de dados se não existir
            if nome_bingo not in stats_bingos:
                stats_bingos[nome_bingo] = {"green": 0, "red": 0}
                
            bingo_deu_red = False
            jogos_computados = 0
            
            for j in jogos_do_bingo:
                chave_jogo = f"{j['time_casa'].strip().lower()}x{j['time_fora'].strip().lower()}"
                
                # Verifica se o robô conseguiu colher o placar desse jogo específico hoje
                if chave_jogo in resultados_jogos:
                    jogos_computados += 1
                    g_c, g_f = resultados_jogos[chave_jogo]
                    # Roda a mesma validação oficial de mercado
                    palpite_correto = validar_palpite(j['mercado'], g_c, g_f)
                    
                    if not palpite_correto:
                        bingo_deu_red = True  # Um único erro derruba o bilhete completo
            
            # Só atualiza se todos os jogos do bilhete foram encontrados e checados
            if jogos_computados == len(jogos_do_bingo):
                if bingo_deu_red:
                    stats_bingos[nome_bingo]["red"] += 1
                    log("RESULTADO BINGO", f"🟥 {nome_bingo} acumulou RED ontem.")
                else:
                    stats_bingos[nome_bingo]["green"] += 1
                    log("RESULTADO BINGO", f"🟩 {nome_bingo} acumulou GREEN (100% de acertos)!")
            else:
                log("AVISO BINGO", f"⚠️ {nome_bingo} não foi computado pois nem todos os placares foram encontrados.")
                
    except Exception as e:
        log("ERRO BINGOS", f"Falha ao conferir os bingos acumulados: {e}")
        
    return stats_bingos

# --- FUNÇÃO ATUALIZADA: GERA O ARQUIVO EM DUAS CATEGORIAS SEPARADAS ---
def gerar_ranking_diario(stats_mercados, stats_bingos):
    log("RANKING", "Gerando novo ranking_diario.json categorizado por chaves...")
    
    ranking_final = {
        "mercados": [],
        "bingos": []
    }
    
    # 1. Monta e ordena a lista de Mercados Simples
    for mercado, dados in stats_mercados.items():
        g = dados.get('green', 0)
        r = dados.get('red', 0)
        total = g + r
        if total > 0:
            ranking_final["mercados"].append({
                "mercado": mercado,
                "green": g,
                "red": r,
                "assertividade": g / total
            })
    ranking_final["mercados"].sort(key=lambda x: (x['assertividade'], x['green']), reverse=True)
    
    # 2. Monta e ordena os Bingos (Fica de forma estática por último)
    for bingo, dados in stats_bingos.items():
        g = dados.get('green', 0)
        r = dados.get('red', 0)
        total = g + r
        ranking_final["bingos"].append({
            "mercado": bingo,
            "green": g,
            "red": r,
            "assertividade": (g / total) if total > 0 else 0.0
        })
    # Mantém os bingos ordenados de forma fixa pelo tipo (Bingo 3, Bingo 5, Premium)
    ranking_final["bingos"].sort(key=lambda x: x['mercado'])
    
    with open(PATH_RANKING_DIARIO, 'w', encoding='utf-8') as f:
        json.dump(ranking_final, f, indent=4, ensure_ascii=False)
    log("RANKING", "Arquivo ranking_diario.json gravado com sucesso em dois blocos.")

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

    hoje_str = date.today().strftime("%Y-%m-%d")

    if data_geracao == hoje_str:
        log("TRAVA", f"O arquivo pendentes.json já é de hoje ({data_geracao}).")
        return

    if not pendentes:
        log("AVISO", "A lista de jogos pendentes está vazia.")
        return

    # Garante o carregamento correto das chaves do banco de dados relacional
    if os.path.exists(PATH_DB):
        with open(PATH_DB, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"stats": {}, "stats_bingos": {}}

    stats = db.get("stats", {})
    stats_bingos = db.get("stats_bingos", {}) # <--- Gaveta exclusiva dos Bingos no Banco
    
    driver = configurar_driver()
    atualizados = 0
    resultados_reais_dia = {} # Dicionário auxiliar para capturar { "time_casaxtime_fora": (gols_c, gols_f) }

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
                    
                    # Alimenta o mapa temporário de gols para a checagem paralela de Bingos
                    chave_mapa = f"{jogo['time_casa'].strip().lower()}x{jogo['time_fora'].strip().lower()}"
                    resultados_reais_dia[chave_mapa] = (g_c, g_f)
                    
                    deu_green = validar_palpite(jogo['mercado'], g_c, g_f)
                    m_rank = jogo['mercado_ranking'].strip().upper()
                    
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

        # --- PROCESSAMENTO EXCLUSIVO DOS BINGOS ACUMULADOS ---
        stats_bingos = conferir_bingos_do_dia(resultados_reais_dia, stats_bingos)

        # --- SALVAMENTO FINAL NO BANCO DE DADOS ---
        db["stats"] = stats
        db["stats_bingos"] = stats_bingos
        db["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        with open(PATH_DB, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        
        # GERA O NOVO RANKING DIÁRIO DIVIDIDO
        gerar_ranking_diario(stats, stats_bingos)
        
        dados_reset = {
            "data_geracao": hoje_str,
            "jogos": []
        }
        with open(PATH_PENDENTES, 'w', encoding='utf-8') as f:
            json.dump(dados_reset, f, indent=4, ensure_ascii=False)
            
        log("FIM", f"Processo concluído. {atualizados} jogos e bilhetes contabilizados.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                                
