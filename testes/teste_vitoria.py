import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def testar_vitoria_casa_final():
    # URL do confronto no FlashScore
    url_teste = "https://www.flashscore.com.br/jogo/futebol/cuiaba-zVvjqDOo/nautico-8ODJnCpa/h2h/total/" 
    
    # Definição dos times conforme o print (Ordem do link é irrelevante)
    t1 = "Náutico"  
    t2 = "Cuiabá"   
    
    driver = configurar_driver()
    print(f"\n🚀 Executando Teste de Validação Real: VITÓRIA CASA")
    print(f"🏟️ Jogo de Hoje -> Mandante (t1): {t1} | Visitante (t2): {t2}")
    print(f"🔗 Link de Análise: {url_teste}\n")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(3)
        
        stats = {
            "t1_resultado_1": "", 
            "t2_resultado_1": "", 
            "h2h_res_1": "",
            "h2h_res_2": ""        
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:3]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")
            if not linhas: continue
            
            # --- TABELA 1: ÚLTIMO JOGO GERAL DO MANDANTE (Náutico) ---
            if idx == 0:
                print("🔎 Analisando Tabela 1 (Momento Imediato do Casa)...")
                for i, linha in enumerate(linhas):
                    status = linha.find_elements(By.CSS_SELECTOR, ".h2h__result")
                    if not status or "postp" in linha.text.lower() or ":" in status[0].text:
                        continue 
                        
                    try:
                        el_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                        el_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        # Sob a ótica de quem é t1 (Náutico)
                        if t1.lower() in el_casa.text.lower() or "nautico" in el_casa.text.lower():
                            res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        else:
                            res = "V" if g2 > g1 else ("D" if g2 < g1 else "E")
                            
                        stats["t1_resultado_1"] = res
                        print(f"   🏠 [MATCH ÚLTIMO JOGO] {el_casa.text.strip()} {g1}-{g2} {el_fora.text.strip()} ➔ Letra: {res}")
                        break
                    except: continue

            # --- TABELA 2: ÚLTIMO JOGO GERAL DO VISITANTE (Cuiabá) ---
            elif idx == 1:
                print("🔎 Analisando Tabela 2 (Momento Imediato do Fora)...")
                for i, linha in enumerate(linhas):
                    status = linha.find_elements(By.CSS_SELECTOR, ".h2h__result")
                    if not status or "postp" in linha.text.lower() or ":" in status[0].text:
                        continue
                        
                    try:
                        el_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                        el_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        # Sob a ótica de quem é t2 (Cuiabá)
                        if t2.lower() in el_casa.text.lower() or "cuiaba" in el_casa.text.lower():
                            res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        else:
                            res = "V" if g2 > g1 else ("D" if g2 < g1 else "E")
                            
                        stats["t2_resultado_1"] = res
                        print(f"   🚀 [MATCH ÚLTIMO JOGO] {el_casa.text.strip()} {g1}-{g2} {el_fora.text.strip()} ➔ Letra: {res}")
                        break
                    except: continue

            # --- TABELA 3: OS 2 ÚLTIMOS CONFRONTOS DIRETOS (H2H) ---
            elif idx == 2:
                print("🔎 Analisando Tabela 3 (Dois últimos confrontos H2H)...")
                h2h_encontrados = 0
                for i, linha in enumerate(linhas):
                    try:
                        el_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                        el_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        # SEMPRE sob a perspectiva do time da CASA de hoje (t1 = Náutico)
                        if t1.lower() in el_casa.text.lower() or "nautico" in el_casa.text.lower():
                            res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        else:
                            res = "V" if g2 > g1 else ("D" if g2 < g1 else "E")
                        
                        h2h_encontrados += 1
                        if h2h_encontrados == 1:
                            stats["h2h_res_1"] = res
                            print(f"   ⚔️ [H2H JOGO 1] {el_casa.text.strip()} {g1}-{g2} {el_fora.text.strip()} ➔ Letra para o {t1}: {res}")
                        elif h2h_encontrados == 2:
                            stats["h2h_res_2"] = res
                            print(f"   ⚔️ [H2H JOGO 2] {el_casa.text.strip()} {g1}-{g2} {el_fora.text.strip()} ➔ Letra para o {t1}: {res}")
                            break
                    except: continue

        # --- APLICAÇÃO OFICIAL DA SUA REGRA DE NEGÓCIO ---
        casa_ultimo = stats["t1_resultado_1"]
        fora_ultimo = stats["t2_resultado_1"]
        h2h_1 = stats["h2h_res_1"]
        h2h_2 = stats["h2h_res_2"]
        
        valida_momento = (casa_ultimo == "V") and (fora_ultimo in ["E", "D"])
        
        ultimos_dois_h2h = [h2h_1, h2h_2]
        tem_vitoria_h2h = "V" in ultimos_dois_h2h
        tem_derrota_h2h = "D" in ultimos_dois_h2h
        
        vitoria_casa_valida = valida_momento and tem_vitoria_h2h and not tem_derrota_h2h
        
        pct = "N/A"
        if vitoria_casa_valida:
            pct = "100%" if (h2h_1 == "V" and h2h_2 == "V") else "80%"

        print("\n" + "="*75)
        print(f"🔬 CONSOLIDADO FINAL DA VALIDAÇÃO - VITÓRIA CASA")
        print(f"   [PASSO 1] Último {t1} Geral     ➔ Letra: ({casa_ultimo if casa_ultimo else 'NULO'})")
        print(f"   [PASSO 1] Último {t2} Geral     ➔ Letra: ({fora_ultimo if fora_ultimo else 'NULO'})")
        print(f"   [PASSO 2] H2H 1 (Mais Recente) ➔ Letra para o {t1}: ({h2h_1 if h2h_1 else 'NULO'})")
        print(f"   [PASSO 2] H2H 2 (Antigo)       ➔ Letra para o {t1}: ({h2h_2 if h2h_2 else 'NULO'})")
        print("-"*75)
        print(f"   ➔ STATUS MOMENTO IMEDIATO : {'🟩 OK' if valida_momento else '🟥 REJEITADO'}")
        print(f"   ➔ EXISTE DERROTA NO H2H  : {'🟥 SIM (Deveria Barrar)' if tem_derrota_h2h else '🟩 NÃO'}")
        print("-"*75)
        print(f"   🎯 ENTRADA FINAL DO ROBÔ  : {'🟩 VITÓRIA CASA ('+pct+')' if vitoria_casa_valida else '🟥 SEM ENTRADA (MERCADO BARRADO)'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico Executando o Teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_vitoria_casa_final()
      
