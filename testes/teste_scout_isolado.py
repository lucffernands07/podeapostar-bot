import time
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
    url_stats_geral = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas/total"
    
    print("\n🔍 INICIANDO TESTE #34 (MAPEAMENTO TEXTUAL DOS 144 ELEMENTOS)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Estatísticas Totais...")
        driver.get(url_stats_geral)
        time.sleep(5.0)
        
        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
        print(f"📊 Elementos mapeados: {len(todos_spans)}")
        print("\n📝 LISTANDO TEXTOS ENCONTRADOS PARA CORREÇÃO DO FILTRO:")
        print("-" * 60)
        
        for idx, span in enumerate(todos_spans):
            texto = driver.execute_script("return arguments[0].textContent;", span).strip()
            # Mostra apenas textos que não sejam números puros, para isolar os nomes dos scouts
            if texto and not texto.isdigit() and len(texto) > 2:
                print(f"   [Índice {idx:<3}] -> '{texto}'")
                
    except Exception as e:
        print(f"\n❌ Erro na varredura: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE #34")

if __name__ == "__main__":
    rodar_teste_isolado()
    
