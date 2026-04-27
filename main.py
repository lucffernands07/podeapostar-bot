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
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    url = "https://www.flashscore.com.br/jogo/futebol/espanyol-QFfPdh1J/levante-G8FL0ShI/h2h/total/?mid=SKkThKvn"
    time_alvo = "Espanyol"

    try:
        print(f"\n🚀 ACESSANDO: {url}")
        driver.get(url)
        
        # Espera carregar a tabela que a gente sabe que funciona
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        # Pega a última tabela (Confronto Direto)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        secao_direta = secoes[-1] 
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        
        print(f"\n--- DADOS DA 3ª TABELA ({len(linhas)} JOGOS) ---")

        vitorias = 0
        empates = 0
        jogos_contados = 0

        for i, linha in enumerate(linhas[:6]):
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                
                # BUSCA DE GOLS POR POSIÇÃO (Mais estável que split)
                # O Flashscore coloca o primeiro gol num span e o segundo em outro
                gols_elementos = linha.find_element(By.CSS_SELECTOR, ".h2h__result").find_elements(By.TAG_NAME, "span")
                
                if len(gols_elementos) >= 2:
                    val1 = int(gols_elementos[0].text.strip())
                    val2 = int(gols_elementos[1].text.strip())
                else:
                    # Fallback caso venha texto puro (ex: "4-3")
                    txt = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "")
                    import re
                    numeros = re.findall(r'\d+', txt)
                    val1 = int(numeros[0])
                    val2 = int(numeros[1])

                res_final = ""
                # LÓGICA DE ATRIBUIÇÃO
                if val1 == val2:
                    empates += 1
                    res_final = "EMPATE 🤝"
                elif (time_alvo.lower() in casa.lower() and val1 > val2) or \
                     (time_alvo.lower() in fora.lower() and val2 > val1):
                    vitorias += 1
                    res_final = "VITÓRIA ✅"
                else:
                    res_final = "DERROTA ❌"

                print(f"[{i+1}] {casa} {val1}x{val2} {fora} | {time_alvo}: {res_final}")
                jogos_contados += 1

            except Exception as e:
                print(f"⚠️ Erro ao processar linha {i+1}")

        if jogos_contados > 0:
            print("\n" + "="*40)
            print(f"📊 RESUMO FINAL PARA {time_alvo.upper()}:")
            print(f"Vitorias: {vitorias} | Empates: {empates}")
            print(f"Sucesso (1X): {vitorias + empates} de {jogos_contados}")
            print("="*40)

    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
    
