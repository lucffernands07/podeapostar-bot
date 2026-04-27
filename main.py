import time
import re
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
    
    try:
        print(f"\n🚀 ACESSANDO: {url}")
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        secao_direta = secoes[-1] 
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        
        # Variáveis de controle para os dois times
        stats = {
            "time1": {"nome": "Espanyol", "v": 0, "e": 0},
            "time2": {"nome": "Levante", "v": 0, "e": 0}
        }

        print(f"\n--- ANALISANDO IMPACTO DO H2H PARA AMBOS ---")

        for i, linha in enumerate(linhas[:6]):
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                txt_placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                # Extração infalível de números
                nums = re.findall(r'\d+', txt_placar)
                g_casa, g_fora = int(nums[0]), int(nums[1])

                resultado_log = ""
                if g_casa == g_fora:
                    stats["time1"]["e"] += 1
                    stats["time2"]["e"] += 1
                    resultado_log = "🤝 EMPATE (Bom para os dois)"
                elif g_casa > g_fora:
                    # Vitória de quem estava na esquerda (Casa)
                    if stats["time1"]["nome"].lower() in casa.lower():
                        stats["time1"]["v"] += 1
                        resultado_log = f"✅ Vitória {stats['time1']['nome']}"
                    else:
                        stats["time2"]["v"] += 1
                        resultado_log = f"✅ Vitória {stats['time2']['nome']}"
                else:
                    # Vitória de quem estava na direita (Fora)
                    if stats["time1"]["nome"].lower() in fora.lower():
                        stats["time1"]["v"] += 1
                        resultado_log = f"✅ Vitória {stats['time1']['nome']}"
                    else:
                        stats["time2"]["v"] += 1
                        resultado_log = f"✅ Vitória {stats['time2']['nome']}"

                print(f"[{i+1}] {casa} {g_casa}x{g_fora} {fora} | {resultado_log}")

            except: continue

        # RESUMO FINAL COMPARATIVO
        print("\n" + "="*45)
        for t in ["time1", "time2"]:
            nome = stats[t]["nome"]
            v, e = stats[t]["v"], stats[t]["e"]
            sucesso_1x = v + e
            print(f"📊 {nome.upper()}: {v}V - {e}E | Sucesso 1X: {sucesso_1x}/5")
        print("="*45)

    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
    
