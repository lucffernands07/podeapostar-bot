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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

def testar_nova_logica_mando():
    url_teste = "https://www.flashscore.com.br/jogo/futebol/al-hazm-YZFeqj3D/al-taawon-WjJkJilj/h2h/total/"
    t1, t2 = "Al Hazm", "Al-Taawon"
    
    driver = configurar_driver()
    print(f"\n🚀 Validando Nova Regra de Mando de Campo: {t1} x {t2}")
    print(f"🔗 Link Alvo: {url_teste}")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(3)
        
        stats = {
            "t1_resultado_1": "", 
            "t2_resultado_1": "", 
            "h2h_res_1": ""        
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # ---------------------------------------------------------------------
        # SEÇÃO 0: JOGOS DO CASA -> Al Hazm precisa ser MANDANTE (Time de Cima)
        # ---------------------------------------------------------------------
        if len(secoes) > 0:
            linhas = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                try:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip()
                    n_fora = times_linha[1].text.strip()
                    
                    # Se o Al Hazm for o time de cima, achamos o jogo de casa legítimo!
                    if t1.lower() in n_casa.lower():
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        if g1 > g2: res = "V"
                        elif g1 < g2: res = "D"
                        else: res = "E"
                        
                        stats["t1_resultado_1"] = res
                        print(f"   🏠 [PASSO 1] Casa em Casa Encontrado: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {res}")
                        break # Só para se gravar o resultado com sucesso
                except Exception:
                    continue

        # ---------------------------------------------------------------------
        # SEÇÃO 1: JOGOS DO FORA -> Al-Taawon precisa ser VISITANTE (Time de Baixo)
        # ---------------------------------------------------------------------
        if len(secoes) > 1:
            linhas = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                try:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip()
                    n_fora = times_linha[1].text.strip()
                    
                    # Se o Al-Taawon for o time de baixo, achamos o jogo fora legítimo!
                    if t2.lower() in n_fora.lower():
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        if g2 > g1: res = "V"
                        elif g2 < g1: res = "D"
                        else: res = "E"
                        
                        stats["t2_resultado_1"] = res
                        print(f"   🚀 [PASSO 2] Fora Fora Encontrado: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {res}")
                        break # Só para se gravar o resultado com sucesso
                except Exception:
                    continue

        # ---------------------------------------------------------------------
        # SEÇÃO 2: CONFRONTOS DIRETOS (H2H) -> Al Hazm em CIMA (Mandante)
        # ---------------------------------------------------------------------
        if len(secoes) > 2:
            linhas = secoes[2].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                try:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip()
                    n_fora = times_linha[1].text.strip()
                    
                    if t1.lower() in n_casa.lower():
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        if g1 > g2: res = "V"
                        elif g1 < g2: res = "D"
                        else: res = "E"
                        
                        stats["h2h_res_1"] = res
                        print(f"   ⚔️ [PASSO 3] H2H na Casa: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {res}")
                        break
                except Exception:
                    continue

        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]
        dados_ok = (ucc != "" and uff != "" and uh2h != "")

        trava_1x = ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_ok

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA NOVA - MERCADO: 1X")
        print(f"   [PASSO 1] Casa em Casa ({ucc if ucc else 'NULO'})")
        print(f"   [PASSO 2] Fora Fora    ({uff if uff else 'NULO'})")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h if uh2h else 'NULO'})")
        print(f"   ➔ RESULTADO 1X: {'🟩 GREEN LIGHT (Aprovado)' if trava_1x else '🟥 BLOQUEADO'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_nova_logica_mando()
        
