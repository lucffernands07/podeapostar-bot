import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def realizar_teste_h2h_especifico():
    # Configurações do Driver
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Opcional: rodar sem abrir a janela
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    id_jogo = "QFfPdh1J" # ID do jogo Espanyol x Levante
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    
    try:
        print(f"\n🚀 Acessando: {url_h2h}")
        driver.get(url_h2h)
        time.sleep(6) # Tempo para carregar os elementos e scripts

        # Localizar as seções H2H (Geralmente: 1. Casa, 2. Fora, 3. Direto)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        if len(secoes) < 3:
            print("❌ ERRO: Seção de Confronto Direto não encontrada.")
            return

        # Focar no Confronto Direto (Seção 3)
        confronto_direto = secoes[2]
        print(f"✅ Seção 'Confronto Direto' identificada.")

        # Tentar expandir para garantir que temos os 5 jogos
        try:
            btn_mais = confronto_direto.find_element(By.CSS_SELECTOR, "span[class*='showMore']")
            driver.execute_script("arguments[0].click();", btn_mais)
            print("➕ Expandindo histórico para ver mais jogos...")
            time.sleep(2)
        except:
            print("ℹ️ Lista já expandida ou botão não necessário.")

        linhas = confronto_direto.find_elements(By.CSS_SELECTOR, ".h2h__row")
        print(f"\n--- ANALISANDO ÚLTIMOS {len(linhas)} CONFRONTOS ---")

        vitorias_casa = 0
        empates = 0
        derrotas_casa = 0

        for i, linha in enumerate(linhas[:6]): # Analisa até os últimos 6 jogos
            try:
                # Captura dados básicos
                time_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                time_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                # IDENTIFICAÇÃO PELO ÍCONE (COR/CLASSE)
                icones = linha.find_elements(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                resultado_final = "Indefinido"
                
                if icones:
                    classe = icones[0].get_attribute("class").lower()
                    
                    # Verifica a classe CSS (Win, Draw, Loss)
                    if 'win' in classe or 'w' in classe:
                        vitorias_casa += 1
                        resultado_final = "VITÓRIA ✅"
                    elif 'draw' in classe or 'd' in classe:
                        empates += 1
                        resultado_final = "EMPATE 🤝"
                    elif 'loss' in classe or 'l' in classe:
                        derrotas_casa += 1
                        resultado_final = "DERROTA ❌"

                print(f"Jogo {i+1}: {time_casa} {placar} {time_fora} | Resultado: {resultado_final}")

            except Exception as e:
                print(f"⚠️ Erro na linha {i+1}: {e}")

        print("\n" + "="*30)
        print("📊 RESUMO PARA O ROBÔ:")
        print(f"Total de jogos lidos: {i+1}")
        print(f"Vitórias (para Vitória Casa): {vitorias_casa}")
        print(f"Sucessos (para 1X): {vitorias_casa + empates}")
        print(f"Taxa de Sucesso 1X: {((vitorias_casa + empates)/(i+1))*100:.1f}%")
        print("="*30)

    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        print("\nFim do teste. O driver será fechado em 15 segundos.")
        time.sleep(15)
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
    
