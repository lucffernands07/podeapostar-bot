import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Usando a URL de estatísticas totais (idêntica à estratégia de cartões)
    url_stats_geral = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas/total"
    
    print("\n🎯 INICIANDO TESTE #33 (MÉTODO DE CARTÕES PARA FINALIZAÇÕES COLETIVAS)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Estatísticas Totais...")
        driver.get(url_stats_geral)
        time.sleep(4.0)
        
        finalizacoes_totais_jogo = 0
        finalizacoes_no_alvo_jogo = 0
        
        # Captura todos os blocos de texto idênticos ao método de cartões
        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
        print(f"📊 Elementos de texto mapeados na página: {len(todos_spans)}")
        
        for idx, span in enumerate(todos_spans):
            texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
            
            # Buscando os termos coletivos de chutes
            if texto_elemento in ["TOTAL DE FINALIZAÇÕES", "FINALIZAÇÕES", "TOTAL ATTEMPTS", "REMATES"]:
                if idx > 0 and (idx + 1) < len(todos_spans):
                    val_casa = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                    val_fora = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                    
                    chutes_casa = int(re.search(r'\d+', val_casa).group()) if re.search(r'\d+', val_casa) else 0
                    chutes_fora = int(re.search(r'\d+', val_fora).group()) if re.search(r'\d+', val_fora) else 0
                    finalizacoes_totais_jogo = chutes_casa + chutes_fora
                    print(f"   🔥 [DETECTADO] Total de Finalizações -> Mandante: {chutes_casa} | Visitante: {chutes_fora} (Total: {finalizacoes_totais_jogo})")
            
            elif texto_elemento in ["FINALIZAÇÕES NO ALVO", "CHUTES NO GOL", "SHOTS ON GOAL", "REMATES À BALIZA"]:
                if idx > 0 and (idx + 1) < len(todos_spans):
                    val_casa_alvo = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                    val_fora_alvo = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                    
                    alvo_casa = int(re.search(r'\d+', val_casa_alvo).group()) if re.search(r'\d+', val_casa_alvo) else 0
                    alvo_fora = int(re.search(r'\d+', val_fora_alvo).group()) if re.search(r'\d+', val_fora_alvo) else 0
                    finalizacoes_no_alvo_jogo = alvo_casa + alvo_fora
                    print(f"   🎯 [DETECTADO] Finalizações no Alvo -> Mandante: {alvo_casa} | Visitante: {alvo_fora} (Total: {finalizacoes_no_alvo_jogo})")

        print("-" * 60)
        print(f"🚀 SCOUTS COLETIVOS FINAIS: Totais: {finalizacoes_totais_jogo} | No Alvo: {finalizacoes_no_alvo_jogo}")

    except Exception as e:
        print(f"\n❌ Erro ao processar dados pelo método de cartões: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #33")

if __name__ == "__main__":
    rodar_teste_isolado()
                
