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
    time_alvo = "Espanyol" # O time que estamos analisando

    try:
        print(f"\n🚀 ACESSANDO: {url}")
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        secao_direta = secoes[-1] 
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        
        print(f"\n--- ANALISANDO CONFRONTOS DIRETOS PARA: {time_alvo} ---")

        vitorias = 0
        empates = 0
        total_jogos = 0

        for i, linha in enumerate(linhas[:6]):
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                placar_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text # Ex: "4 - 3" ou "1 - 1"
                
                # Limpa o placar e separa os números
                gols = placar_texto.replace("\n", "").replace(" ", "").split("-")
                gols_casa = int(gols[0])
                gols_fora = int(gols[1])

                resultado = ""
                # LÓGICA DE PLACAR REAL
                if gols_casa == gols_fora:
                    empates += 1
                    resultado = "EMPATE 🤝"
                elif time_alvo in casa and gols_casa > gols_fora:
                    vitorias += 1
                    resultado = "VITÓRIA ✅"
                elif time_alvo in fora and gols_fora > gols_casa:
                    vitorias += 1
                    resultado = "VITÓRIA ✅"
                else:
                    resultado = "DERROTA ❌"

                print(f"[{i+1}] {casa} {gols_casa}-{gols_fora} {fora} | Resultado para {time_alvo}: {resultado}")
                total_jogos += 1

            except Exception as e:
                print(f"⚠️ Erro ao processar linha {i+1}")

        # Resumo Final
        taxa_1x = ((vitorias + empates) / total_jogos) * 100
        print("\n" + "="*40)
        print(f"📊 RELATÓRIO FINAL:")
        print(f"Total de jogos: {total_jogos}")
        print(f"Vitórias: {vitorias} | Empates: {empates}")
        print(f"Taxa de Sucesso (1X): {taxa_1x:.1f}%")
        print("="*40)

    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
    
