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
    print(f"\n🚀 Validando Nova Regra de Mando por Títulos de Seção: {t1} x {t2}")
    print(f"🔗 Link Alvo: {url_teste}")
    
    t1_limpo = t1.lower().replace("-", " ").strip()
    t2_limpo = t2.lower().replace("-", " ").strip()
    
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
        print(f"📦 Total de blocos .h2h__section detectados: {len(secoes)}")
        
        for secao in secoes:
            try:
                # Pega o título da seção para saber de quem são os jogos
                titulo_el = secao.find_element(By.CSS_SELECTOR, ".section__title, .h2h__sectionHeader")
                titulo_txt = titulo_el.text.lower()
            except:
                continue
                
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")
            if not linhas: continue

            # -----------------------------------------------------------------
            # CASO A: Seção de últimos jogos do TIME DA CASA (Al Hazm)
            # -----------------------------------------------------------------
            if t1_limpo in titulo_txt and "confrontos" not in titulo_txt:
                print(f"🔎 Varrendo a seção identificada do Mandante: '{titulo_el.text}'")
                for linha in linhas:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip().lower().replace("-", " ")
                    n_fora = times_linha[1].text.strip().lower().replace("-", " ")
                    
                    if t1_limpo in n_casa: # Al Hazm como mandante legítimo (cima)
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        stats["t1_resultado_1"] = res
                        print(f"   🏠 [PASSO 1] Encontrado: {times_linha[0].text.strip()} {g1}-{g2} {times_linha[1].text.strip()} ➔ Letra: {res}")
                        break

            # -----------------------------------------------------------------
            # CASO B: Seção de últimos jogos do TIME DE FORA (Al-Taawon)
            # -----------------------------------------------------------------
            elif t2_limpo in titulo_txt and "confrontos" not in titulo_txt:
                print(f"🔎 Varrendo a seção identificada do Visitante: '{titulo_el.text}'")
                for linha in linhas:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip().lower().replace("-", " ")
                    n_fora = times_linha[1].text.strip().lower().replace("-", " ")
                    
                    if t2_limpo in n_fora: # Al-Taawon como visitante legítimo (baixo)
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g2 > g1 else ("D" if g2 < g1 else "E")
                        stats["t2_resultado_1"] = res
                        print(f"   🚀 [PASSO 2] Encontrado: {times_linha[0].text.strip()} {g1}-{g2} {times_linha[1].text.strip()} ➔ Letra: {res}")
                        break

            # -----------------------------------------------------------------
            # CASO C: Seção de CONFRONTOS DIRETOS (H2H)
            # -----------------------------------------------------------------
            elif "confrontos" in titulo_txt or "h2h" in titulo_txt:
                print(f"🔎 Varrendo a seção identificada de Confrontos Diretos: '{titulo_el.text}'")
                for linha in linhas:
                    times_linha = linha.find_elements(By.CSS_SELECTOR, ".h2h__participantInner")
                    if len(times_linha) < 2: continue
                    
                    n_casa = times_linha[0].text.strip().lower().replace("-", " ")
                    
                    if t1_limpo in n_casa: # Al Hazm jogando na casa dele contra o Al-Taawon
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        stats["h2h_res_1"] = res
                        print(f"   ⚔️ [PASSO 3] Encontrado: {times_linha[0].text.strip()} {g1}-{g2} {times_linha[1].text.strip()} ➔ Letra: {res}")
                        break

        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]
        dados_ok = (ucc != "" and uff != "" and uh2h != "")

        trava_1x = ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_ok

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DINÂMICA - MERCADO: 1X")
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
                        
