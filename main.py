import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def realizar_teste_h2h_especifico():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # User-agent para simular navegador real e evitar bloqueio parcial
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    # URL direta que você passou
    url = "https://www.flashscore.com.br/jogo/futebol/espanyol-QFfPdh1J/levante-G8FL0ShI/h2h/total/?mid=SKkThKvn"
    
    try:
        print(f"\n🚀 ACESSANDO: {url}")
        driver.get(url)

        # 1. Esperar carregar qualquer linha de H2H para garantir que a página abriu
        print("⏳ Aguardando carregamento dos dados...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        # 2. Pegar todas as seções H2H disponíveis
        # No Flashscore, a 3ª tabela (Confrontos Diretos) é a última .h2h__section
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        print(f"📊 Tabelas detectadas: {len(secoes)}")

        if len(secoes) < 3:
            print("⚠️ Apenas uma tabela carregou. Tentando forçar scroll para liberar o restante...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")

        # Selecionamos a última seção (que conforme o print e a URL é o Confronto Direto)
        secao_direta = secoes[-1] 
        
        # 3. Raspar os dados das linhas
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        print(f"\n--- DADOS DA 3ª TABELA ({len(linhas)} JOGOS) ---")

        vitorias_t1 = 0
        empates = 0

        for i, linha in enumerate(linhas[:6]): # Pega os últimos 6 confrontos
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                # Identificação pela cor do ícone (Win/Draw/Loss)
                icones = linha.find_elements(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                resultado = "N/A"
                
                if icones:
                    classe = icones[0].get_attribute("class").lower()
                    if 'win' in classe or 'w' in classe:
                        vitorias_t1 += 1
                        resultado = "VITÓRIA"
                    elif 'draw' in classe or 'd' in classe:
                        empates += 1
                        resultado = "EMPATE"
                    else:
                        resultado = "DERROTA"

                print(f"[{i+1}] {casa} {placar} {fora} | {resultado}")

            except Exception as e:
                print(f"⚠️ Erro na linha {i+1}")

        # Resumo
        total = i + 1
        print("\n" + "="*40)
        print(f"✅ SUCESSO NA RASPAGEM")
        print(f"Total analisado: {total}")
        print(f"Vitórias + Empates: {vitorias_t1 + empates}")
        print("="*40)

    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        driver.save_screenshot("debug_h2h_github.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
