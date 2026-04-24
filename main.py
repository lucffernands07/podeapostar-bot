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
    """Navega para o jogo e extrai o texto bruto das estatísticas"""
    url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo_h2h}/#/resumo-de-jogo"
    print(f"\n    --- ANALISANDO JOGO: {id_jogo_h2h} ---")
    
    driver.get(url_jogo)
    total_cantos = 0
    try:
        # 1. Espera o menu e clica em Estatísticas
        btn_stats = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Estatísticas')]"))
        )
        driver.execute_script("arguments[0].click();", btn_stats)
        
        # 2. Aguarda o card carregar
        time.sleep(4) 

        # 3. Captura o texto bruto de todo o container de estatísticas
        # Usamos o seletor de seção para garantir que pegamos o bloco central
        container = driver.find_element(By.CSS_SELECTOR, "div[id*='statistics']")
        texto_bruto = container.text.replace('\n', ' | ')
        
        # LOG DO BRUTO (O que você pediu)
        print(f"    [DADOS BRUTOS]: {texto_bruto}")

        # 4. Extração via Regex no texto bruto para garantir os cantos
        # Procura o padrão: Numero | Escanteios | Numero
        match = re.search(r'(\d+) \| Escanteios \| (\d+)', texto_bruto)
        if match:
            c_casa = int(match.group(1))
            c_fora = int(match.group(2))
            total_cantos = c_casa + c_fora
            print(f"    ✅ EXTRAÍDO COM SUCESSO: {total_cantos} cantos.")
    except Exception as e:
        print(f"    ⚠️ Erro ao processar dados: {str(e)[:50]}")
        
    return total_cantos

def pegar_estatisticas_h2h(driver, url_jogo):
    print(f"\n[ABA H2H] Abrindo confronto: {url_jogo}")
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "casa_15": 0, "casa_25": 0, "casa_45": 0, "casa_btts": 0, "casa_ult_btts": False, 
        "casa_ult_15": False, "casa_ult_sofreu": False, "casa_derrotas": 0, "casa_ult_res": "",
        "fora_15": 0, "fora_25": 0, "fora_45": 0, "fora_btts": 0, "fora_ult_btts": False,
        "fora_ult_15": False, "fora_ult_sofreu": False, "fora_derrotas": 0, "fora_ult_res": "",
        "pular_gols": False, "ids_h2h": [] 
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(8)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for idx, secao in enumerate(secoes[:2]):
            prefixo = "casa" if idx == 0 else "fora"
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            
            for i, linha in enumerate(linhas):
                try:
                    # Captura o ID do link ou da linha
                    id_raw = linha.get_attribute("id")
                    if not id_raw:
                        id_raw = linha.find_element(By.TAG_NAME, "a").get_attribute("id")
                    
                    id_limpo = id_raw.split('_')[-1] if id_raw else ""
                    if id_limpo:
                        stats["ids_h2h"].append(id_limpo)
                except: pass

                try:
                    res_icon = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip().upper()
                    if i == 0: stats[f"{prefixo}_ult_res"] = res_icon
                    if res_icon == "D": stats[f"{prefixo}_derrotas"] += 1
                except: pass

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
                    
        print(f"[ABA H2H] Sucesso na coleta.")
    except Exception as e:
        print(f"[ABA H2H] Erro: {e}")
        
    return stats

def main():
    driver = configurar_driver()
    id_teste = "ne5y23mR"
    url_confronto = f"https://www.flashscore.com.br/jogo/{id_teste}/#/h2h/overall"
    
    print(f"🚀 INICIANDO DIAGNÓSTICO BRUTO - JOGO: {id_teste}")
    
    try:
        driver.get("https://www.flashscore.com.br/")
        time.sleep(5)
        
        s = pegar_estatisticas_h2h(driver, url_confronto)
        
        # Debug: Confirmar que os IDs foram salvos na lista antes de prosseguir
        ids_finais = list(dict.fromkeys([x for x in s["ids_h2h"] if x]))
        print(f"DEBUG: IDs encontrados: {ids_finais}")
        
        res_gols = gols.verificar_gols(s)
        res_cd = chance_dupla.verificar_chance_dupla(s)
        print(f"✅ MERCADOS: {res_gols + res_cd}")
        
        if ids_finais:
            print(f"\n🔍 BUSCANDO DADOS BRUTOS EM {len(ids_finais)} JOGOS...")
            soma_c, cont_j = 0, 0
            
            # Garante que volta para a primeira aba antes de navegar linearmente
            driver.switch_to.window(driver.window_handles[0])

            for id_h in ids_finais:
                c = capturar_escanteios_detalhe(driver, id_h)
                if c > 0:
                    soma_c += c
                    cont_j += 1
            
            if cont_j > 0:
                print(f"\n📊 MÉDIA FINAL DE CANTOS: {soma_c / cont_j:.2f}")
        else:
            print("❌ LISTA DE IDs VAZIA NO H2H.")

    finally:
        print("\n🏁 FIM DO TESTE.")
        driver.quit()

if __name__ == "__main__":
    main()
          
