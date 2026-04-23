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

# Importação dos seus módulos
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
        # 1. Espera o botão Estatísticas
        btn_stats = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Estatísticas')]"))
        )
        driver.execute_script("arguments[0].click();", btn_stats)
        
        # 2. Tempo para carregar os números (Flashscore é lento aqui)
        time.sleep(4) 

        # 3. Localiza a linha de escanteios pelo texto central
        xpath_cantos = "//div[contains(@class, 'stat__category') and .//div[contains(text(), 'Escanteios')]]"
        linha = driver.find_element(By.XPATH, xpath_cantos)
        
        numeros = re.findall(r'\d+', linha.text)
        if len(numeros) >= 2:
            c_casa = int(numeros[0])
            c_fora = int(numeros[1])
            total_cantos = c_casa + c_fora
            print(f"    [ABA DETALHE] ✅ Cantos encontrados: {total_cantos} ({c_casa} + {c_fora})")
    except Exception as e:
        print(f"    [ABA DETALHE] ⚠️ Escanteios não localizados neste jogo.")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[1]) # Volta para a aba H2H
    return total_cantos

            for i, linha in enumerate(linhas):
                # Captura os IDs para os escanteios (MELHORADO)
                try:
                    # Tenta pegar do ID da linha ou do link direto do jogo
                    id_raw = linha.get_attribute("id") 
                    if not id_raw: # Caso o ID falhe, tenta pegar do link do clique
                        id_raw = linha.find_element(By.TAG_NAME, "a").get_attribute("id")
                    
                    id_limpo = id_raw.split('_')[-1]
                    if id_limpo:
                        stats["ids_h2h"].append(id_limpo)
                        print(f"      [H2H] ID capturado: {id_limpo}") # Log para confirmar
                except: 
                    pass

def main():
    driver = configurar_driver()
    # Teste no jogo: Defensa y Justicia x Boca Juniors
    id_teste = "ne5y23mR" 
    url_confronto = f"https://www.flashscore.com.br/jogo/{id_teste}/#/h2h/overall"
    
    print(f"🚀 INICIANDO DIAGNÓSTICO COMPLETO - JOGO: {id_teste}")
    
    try:
        driver.get("https://www.flashscore.com.br/")
        time.sleep(5)
        
        # 1. Análise de H2H
        s = pegar_estatisticas_h2h(driver, url_confronto)
        
        # 2. Execução dos Mercados
        res_gols = gols.verificar_gols(s)
        res_btts = ambos_marcam.verificar_btts(s)
        res_cd = chance_dupla.verificar_chance_dupla(s)
        
        sugestoes = res_gols + ([f"Ambas Marcam ({res_btts})"] if res_btts else []) + res_cd
        print(f"\n✅ MERCADOS ANALISADOS: {sugestoes}")
        
        # 3. Varredura de Cantos (se houver IDs)
        if s["ids_h2h"]:
            print(f"\n🔍 INICIANDO BUSCA DE ESCANTEIOS EM {len(s['ids_h2h'])} JOGOS...")
            soma_c, cont_j = 0, 0
            
            for id_h in s["ids_h2h"]:
                c = capturar_escanteios_detalhe(driver, id_h)
                if c > 0:
                    soma_c += c
                    cont_j += 1
            
            media = soma_c / cont_j if cont_j > 0 else 0
            print(f"\n📊 --- RELATÓRIO FINAL ---")
            print(f"   > Total de Cantos Somados: {soma_c}")
            print(f"   > Jogos com Estatísticas: {cont_j}")
            print(f"   > MÉDIA FINAL DE CANTOS: {media:.2f}")
        else:
            print("\n❌ Nenhum ID de jogo foi encontrado no H2H.")

    finally:
        print("\n🏁 TESTE ENCERRADO - VERIFIQUE OS LOGS ACIMA")
        driver.quit()

if __name__ == "__main__":
    main()
    
