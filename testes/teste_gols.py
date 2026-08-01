import os
import sys
import time
import re

# Garantir acesso aos módulos da raiz e funcoes sem erro de import
PASTA_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PASTA_RAIZ not in sys.path:
    sys.path.insert(0, PASTA_RAIZ)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from mercados import gols

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
    url_teste = "https://www.flashscore.com.br/jogo/futebol/remo-2i0B6Zul/santos-n3QdnjFB/h2h/total/"
    t1_nome, t2_nome = "Remo", "Santos"
    
    url_limpa = url_teste.rstrip("/")
    if "/h2h" in url_limpa:
        url_base = url_limpa.split("/h2h")[0] + "/h2h"
    else:
        url_base = url_limpa + "/h2h"

    url_total = f"{url_base}/total/"
    url_casa = f"{url_base}/casa/"
    url_fora = f"{url_base}/fora/"

    driver = configurar_driver()
    print(f"\n🚀 Teste Exclusivo de Gols: {t1_nome} x {t2_nome}")
    
    try:
        stats = {
            "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0,
            "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0,
            "ultimo_gols_casa": 0, "ultimo_gols_fora": 0,
            "h2h_placar_1": "" 
        }

        # --- PARTE 1: CONFRONTO DIRETO HISTÓRICO (3ª TABELA DA ABA TOTAL) ---
        print(f"\n⚔️ Raspando 3ª Tabela (H2H Direto) na aba TOTAL...")
        driver.get(url_total)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
            secoes_total = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
            if len(secoes_total) >= 3:
                linhas_h2h = secoes_total[2].find_elements(By.CSS_SELECTOR, ".h2h__row")
                if linhas_h2h:
                    res_el = linhas_h2h[0].find_elements(By.CSS_SELECTOR, ".h2h__result")
                    if res_el:
                        stats["h2h_placar_1"] = res_el[0].text
                        print(f"   ➔ Último confronto H2H (3ª Tabela): '{stats['h2h_placar_1']}'")
            else:
                print("   ⚠️ 3ª tabela de H2H não foi encontrada na aba Total.")
        except Exception as e_h2h:
            print(f"   ⚠️ Falha ao raspar 3ª tabela de H2H: {e_h2h}")

        # --- PARTE 2: RASPAR JOGOS DE CASA (/h2h/casa/) ---
        print(f"\n📊 Analisando jogos em CASA de {t1_nome}...")
        driver.get(url_casa)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        secoes_casa = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        if secoes_casa:
            linhas_casa = secoes_casa[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for i, linha in enumerate(linhas_casa):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    print(f"   Jogo {i+1} (Casa): Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0: stats["ultimo_gols_casa"] = total
                    if total > 1.5: stats["casa_15"] += 1
                    if total > 2.5: stats["casa_25"] += 1
                    if total <= 3: stats["casa_35_under"] += 1
                    if total <= 4: stats["casa_45_under"] += 1

        # --- PARTE 3: RASPAR JOGOS DE FORA (/h2h/fora/) ---
        print(f"\n📊 Analisando jogos FORA de {t2_nome}...")
        driver.get(url_fora)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        secoes_fora = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        if secoes_fora:
            linhas_fora = secoes_fora[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for i, linha in enumerate(linhas_fora):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    print(f"   Jogo {i+1} (Fora): Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0: stats["ultimo_gols_fora"] = total
                    if total > 1.5: stats["fora_15"] += 1
                    if total > 2.5: stats["fora_25"] += 1
                    if total <= 3: stats["fora_35_under"] += 1
                    if total <= 4: stats["fora_45_under"] += 1

        print("\n--- DICIONÁRIO ENVIADO PARA O MÓDULO GOLS.PY ---")
        print(stats)

        # --- PARTE 4: PROCESSAMENTO VIA MERCADOS/GOLS.PY ---
        print("\n--- MERCADOS DE GOLS APROVADOS PELO MÓDULO (GOLS.PY) ---")
        res_gols = gols.verificar_gols(stats)
        
        if not res_gols:
            print("❌ Módulo GOLS.PY reprovou todas as entradas de gols para este jogo.")
        else:
            for item in res_gols:
                print(f"💰 MERCADO APROVADO: {item['mercado']} | Tipo: {item['tipo']}")

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste concluído.")

if __name__ == "__main__":
    testar_jogo_especifico()
        
