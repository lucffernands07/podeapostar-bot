import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importação dos seus módulos (mantidos conforme seu projeto)
from mercados import gols, ambos_marcam, chance_dupla

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def capturar_escanteios_detalhe(driver, id_jogo_h2h):
    url_detalhe = f"https://www.flashscore.com.br/jogo/{id_jogo_h2h}/#/resumo-de-jogo/estatisticas-de-jogo"
    print(f"    [ABA DETALHE] Acessando ID: {id_jogo_h2h}")
    driver.execute_script(f"window.open('{url_detalhe}', '_blank');")
    
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) >= 3)
    driver.switch_to.window(driver.window_handles[-1])
    
    total_cantos = 0
    try:
        # Tenta clicar no botão Estatísticas
        btn_stats = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Estatísticas')]"))
        )
        driver.execute_script("arguments[0].click();", btn_stats)
        print(f"    [ABA DETALHE] Botão Estatísticas clicado.")
        
        time.sleep(4) # Tempo para carregar os números

        # Tenta localizar a linha de escanteios
        xpath_cantos = "//div[contains(@class, 'stat__category') and .//div[contains(text(), 'Escanteios')]]"
        linha = driver.find_element(By.XPATH, xpath_cantos)
        
        numeros = re.findall(r'\d+', linha.text)
        if len(numeros) >= 2:
            total_cantos = int(numeros[0]) + int(numeros[1])
            print(f"    [ABA DETALHE] ✅ Cantos encontrados: {total_cantos} ({numeros[0]} + {nums[1]})")
    except Exception as e:
        print(f"    [ABA DETALHE] ⚠️ Não encontrou escanteios. Erro: {str(e)[:50]}")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[1]) # Volta para o H2H
    return total_cantos

def pegar_estatisticas_h2h(driver, url_jogo):
    print(f"\n[ABA H2H] Abrindo confronto: {url_jogo}")
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "casa_15": 0, "casa_25": 0, "casa_45": 0, "casa_btts": 0, "casa_ult_btts": False, 
        "casa_ult_15": False, "casa_ult_sofreu": False,
        "fora_15": 0, "fora_25": 0, "fora_45": 0, "fora_btts": 0, "fora_ult_btts": False,
        "fora_ult_15": False, "fora_ult_sofreu": False,
        "pular_gols": False, "ids_h2h": [] 
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        print("[ABA H2H] Aba H2H clicada. Aguardando carregamento...")
        time.sleep(8)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for idx, secao in enumerate(secoes[:2]):
            prefixo = "casa" if idx == 0 else "fora"
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            
            for i, linha in enumerate(linhas):
                try:
                    id_h = linha.get_attribute("id").split('_')[-1]
                    stats["ids_h2h"].append(id_h)
                except: pass
                
                # Lógica de processamento de gols e btts (mantida do seu original)
                texto = linha.text.replace('\n', ' ')
                nums = [int(n) for n in re.findall(r'\d+', texto)]
                if len(nums) >= 2:
                    g1, g2 = nums[-2], nums[-1]
                    total = g1 + g2
                    if i == 0:
                        if idx == 0 and (total <= 1): stats["pular_gols"] = True
                        stats[f"{prefixo}_ult_15"] = (total > 1.5)
                        stats[f"{prefixo}_ult_sofreu"] = (g2 > 0)
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_ult_btts"] = True
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if total <= 4: stats[f"{prefixo}_45"] += 1 
                    if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1
        print(f"[ABA H2H] IDs coletados: {len(stats['ids_h2h'])} jogos encontrados.")
    except Exception as e:
        print(f"[ABA H2H] Erro: {e}")
        
    return stats

def main():
    driver = configurar_driver()
    # ID FIXO: Defensa y Justicia x Boca Juniors
    id_teste = "ne5y23mR" 
    url_confronto = f"https://www.flashscore.com.br/jogo/{id_teste}/#/h2h/overall"
    
    print(f"🚀 INICIANDO DIAGNÓSTICO COMPLETO - JOGO: {id_teste}")
    
    try:
        driver.get("https://www.flashscore.com.br/") # Abre a home primeiro
        time.sleep(5)
        
        # 1. Executa a análise de H2H
        s = pegar_estatisticas_h2h(driver, url_confronto)
        
        # 2. Roda os seus módulos de mercado
        res_gols = gols.verificar_gols(s)
        res_btts = ambos_marcam.verificar_btts(s)
        res_cd = chance_dupla.verificar_chance_dupla(s)
        
        sugestoes = res_gols + ([f"Ambas Marcam ({res_btts})"] if res_btts else []) + res_cd
        print(f"\n✅ MERCADOS APROVADOS: {sugestoes}")
        
        if sugestoes:
            print("\n🔍 INICIANDO VARREDURA DE ESCANTEIOS NOS 10 JOGOS...")
            soma_c, cont_j = 0, 0
            
            # Percorre os IDs coletados no H2H
            for id_h in s["ids_h2h"]:
                c = capturar_escanteios_detalhe(driver, id_h)
                if c > 0:
                    soma_c += c
                    cont_j += 1
            
            media = soma_c / cont_j if cont_j > 0 else 0
            print(f"\n📊 RESULTADO FINAL DOS ESCANTEIOS:")
            print(f"   > Total de Cantos: {soma_c}")
            print(f"   > Jogos com dados: {cont_j}")
            print(f"   > MÉDIA CALCULADA: {media:.2f}")
        else:
            print("\n❌ O jogo não passou nos filtros de mercado. Teste encerrado.")

    finally:
        print("\n🏁 FIM DO LOG DE ACESSO")
        driver.quit()

if __name__ == "__main__":
    main()
