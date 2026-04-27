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
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        secao_direta = secoes[-1] 
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        
        print(f"\n--- PROCESSANDO H2H: {time_alvo} ---")

        vitorias = 0
        empates = 0
        jogos_contados = 0

        for i, linha in enumerate(linhas[:6]):
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                
                # Pega o texto do placar (ex: "4\n-\n3") e remove quebras de linha e espaços
                res_raw = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                res_clean = res_raw.replace("\n", "").replace(" ", "") # Vira "4-3"
                
                partes = res_clean.split("-")
                val1 = int(partes[0])
                val2 = int(partes[1])

                res_final = ""
                # A REGRA QUE VOCÊ DEFINIU:
                if val1 == val2:
                    empates += 1
                    res_final = "EMPATE"
                elif val1 > val2:
                    # Vitória do time da CASA
                    if time_alvo.lower() in casa.lower():
                        vitorias += 1
                        res_final = "VITÓRIA"
                    else:
                        res_final = "DERROTA"
                elif val2 > val1:
                    # Vitória do time de FORA
                    if time_alvo.lower() in fora.lower():
                        vitorias += 1
                        res_final = "VITÓRIA"
                    else:
                        res_final = "DERROTA"

                print(f"[{i+1}] {casa} {val1}x{val2} {fora} -> {time_alvo}: {res_final}")
                jogos_contados += 1

            except Exception as e:
                print(f"⚠️ Erro ao calcular linha {i+1}")

        # Resumo final
        if jogos_contados > 0:
            print("\n" + "="*40)
            print(f"📊 RESULTADO PARA {time_alvo.upper()}:")
            print(f"Vitórias: {vitorias} | Empates: {empates}")
            print(f"Sucessos (1X): {vitorias + empates} de {jogos_contados}")
            print(f"Taxa: {((vitorias + empates)/jogos_contados)*100:.1f}%")
            print("="*40)

    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
    
