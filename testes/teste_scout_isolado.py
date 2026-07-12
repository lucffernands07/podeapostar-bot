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
    
    # Camuflagem para evitar bloqueio headless
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    # 🎯 A URL EXATA DO SEU PRINT (Londrina primeiro, jogo encerrado de 04/07)
    url_real_do_print = "https://www.flashscore.com.br/jogo/futebol/londrina-pr-xdhbBEVA/crb-QHa3bLrj/resumo/estatisticas-jogadores/finalizacoes/"
    
    print("\nCORREÇÃO 🎯 INICIANDO TESTE #41 (URL CORRIGIDA E FIEL AO PRINT DO CELULAR)\n" + "="*60)
    print(f"🔗 URL Alvo na Log: {url_real_do_print}")
    print("="*60)
    
    try:
        driver.get(url_real_do_print)
        print("   Aguardando 7 segundos para carregamento dos dados...")
        time.sleep(7.0) 
        
        # Seletores mapeados por você no HTML
        jogadores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
        valores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
        
        print(f"\n📊 Verificação pós-acesso:")
        print(f"   👤 Jogadores encontrados ('wcl-playerCell'): {len(jogadores)}")
        print(f"   🔢 Valores encontrados ('wcl-tableBodyCell'): {len(valores)}")
        
        if len(jogadores) > 0:
            print("\n📋 DADOS COLETADOS COM SUCESSO:")
            print("-" * 60)
            colunas = len(valores) // len(jogadores) if len(jogadores) > 0 else 0
            
            for idx, jog in enumerate(jogadores[:10]):
                nome = jog.text.split("\n")[0]
                if not nome or "TODOS" in nome.upper(): continue
                
                inicio = idx * colunas
                fim = inicio + colunas
                seus_numeros = [v.text.strip() for v in valores[inicio:fim]]
                print(f"   👤 {nome:<22} | Dados: {seus_numeros}")
        else:
            print("🚨 A página abriu a URL correta, mas a tabela veio zerada no modo headless.")
            
    except Exception as e:
        print(f"\n❌ Erro executivo: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #41")

if __name__ == "__main__":
    rodar_teste_isolado()
    
