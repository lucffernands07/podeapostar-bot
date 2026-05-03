import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Ajuste para importar módulos da pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mercados import gols
import odds

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def testar_jogo_especifico():
    url_teste = "https://www.flashscore.com.br/jogo/futebol/avai-rPzY7fWt/novorizontino-4lOgZPQl/h2h/total/?mid=8pNsVvYg"
    t1_nome, t2_nome = "Novorizontino", "Avai"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando teste: {t1_nome} x {t2_nome}")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        
        # Garante que estamos na aba H2H
        time.sleep(3)
        
        stats = {
            "casa_15": 0, "casa_25": 0, "casa_45_under": 0,
            "fora_15": 0, "fora_25": 0, "fora_45_under": 0,
            "ultimo_gols_casa": 0, "ultimo_gols_fora": 0
        }

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]): # Apenas Casa e Fora
            prefixo = "casa" if idx == 0 else "fora"
            print(f"\n📊 Analisando {prefixo.upper()} ({t1_nome if idx == 0 else t2_nome}):")
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            
            for i, linha in enumerate(linhas):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    
                    # Log individual para conferência
                    print(f"   L{i+1}: Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0:
                        stats[f"ultimo_gols_{prefixo}"] = total
                    
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if total <= 4: stats[f"{prefixo}_45_under"] += 1

        print("\n--- RESUMO DE STATS (Dicionário enviado ao gols.py) ---")
        print(stats)

                # Simula a chamada do módulo de gols
        print("\n--- RESULTADO DO MÓDULO GOLS.PY ---")
        res_gols = gols.verificar_gols(stats)
        
        if not res_gols:
            print("❌ Módulo GOLS.PY não aprovou este jogo.")
        else:
            for r in res_gols:
                # Mudança aqui: acessamos apenas o 'mercado', que já tem a confiança
                print(f"✅ APROVADO: {r['mercado']}")


        # Teste de Odds (Simulado com o ID do jogo da URL)
        id_jogo = "8pNsVvYg" # Extraído manualmente para o teste
        print(f"\n🔍 Buscando Odds para ID: {id_jogo}...")
        v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
        print(f"Odds capturadas: {v_odds}")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_jogo_especifico()
