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
    
    # 🔒 URL FIXA E LITERAL (Sem nenhuma edição ou montagem)
    url_obrigatoria = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/resumo/estatisticas-jogadores/finalizacoes/"
    
    print("\n🎯 INICIANDO TESTE #39 (URL FIXA E ASSESTADA DIRETO DA SUA MENSAGEM)\n" + "="*60)
    print(f"🔗 Acessando exatamente: {url_obrigatoria}")
    
    try:
        driver.get(url_obrigatoria)
        print("   Aguardando 6 segundos para o carregamento completo...")
        time.sleep(6.0) 
        
        # Raspagem direta baseada nos seletores do seu celular
        jogadores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
        valores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
        
        print(f"\n📊 Leitura do DOM terminada:")
        print(f"   👤 Elementos 'wcl-playerCell' (Jogadores): {len(jogadores)}")
        print(f"   🔢 Elementos 'wcl-tableBodyCell' (Valores): {len(valores)}")
        
        if len(jogadores) > 0:
            print("\n📋 LISTANDO OS DADOS ENCONTRADOS:")
            print("-" * 60)
            colunas = len(valores) // len(jogadores) if len(jogadores) > 0 else 0
            
            for idx, jog in enumerate(jogadores[:12]):
                nome = jog.text.split("\n")[0]
                if not nome or "TODOS" in nome.upper(): continue
                
                inicio = idx * colunas
                fim = inicio + colunas
                seus_numeros = [v.text.strip() for v in valores[inicio:fim]]
                
                print(f"   👤 {nome:<22} | Colunas Numéricas: {seus_numeros}")
        else:
            print("🚨 A página carregou, mas a árvore retornou 0 jogadores.")
            
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE #39")

if __name__ == "__main__":
    rodar_teste_isolado()
    
