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
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def testar_trava_dupla_chance():
    # Jogo configurado para teste de X2
    url_teste = "https://www.flashscore.com.br/jogo/WjJkJilj/#/h2h/overall"
    t1, t2 = "Al-Hazm", "Al-Taawon"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando Teste com a Lógica Real do Main: {t1} x {t2}")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        
        # CLIQUE IDÊNTICO AO SEU MAIN.PY
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(3)
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        # Dicionário idêntico ao do seu main.py, mas focado em capturar a letra do primeiro jogo (res_1)
        stats = {
            "t1_resultado_1": "",
            "t2_resultado_1": "",
            "h2h_res_1": ""
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        print(f"📦 Seções H2H encontradas na página: {len(secoes)}")
        
        for idx, secao in enumerate(secoes[:3]): 
            # Captura o limite exatamente igual ao seu main.py
            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            for i, linha in enumerate(linhas):
                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                    
                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    
                    if idx < 2: 
                        t_ref = t1 if idx == 0 else t2
                        
                        # LOGICA DE DESCOBRIR VITÓRIA/EMPATE/DERROTA DO SEU MAIN.PY
                        res_atual = "E"
                        if (t_ref.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t_ref.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_atual = "V"
                        elif (t_ref.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t_ref.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_atual = "D"
                        
                        # Salva o resultado do primeiro jogo (i == 0)
                        if i == 0: 
                            stats[f"t{idx+1}_resultado_1"] = res_atual
                            print(f"   🔹 Seção {idx} (L1) capturada: {n_casa_h2h} {g1}-{g2} {n_fora_h2h} ➔ Letra: {res_atual}")

                    elif idx == 2: 
                        # LOGICA DE DESCOBRIR H2H DO SEU MAIN.PY
                        res_h2h = "E"
                        if (t1.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t1.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_h2h = "V"
                        elif (t1.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t1.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_h2h = "D"
                        
                        if i == 0: 
                            stats["h2h_res_1"] = res_h2h
                            print(f"   🔹 Seção {idx} (H2H L1) capturada: {n_casa_h2h} {g1}-{g2} {n_fora_h2h} ➔ Letra: {res_h2h}")

                except Exception as e: 
                    continue

        # Extração das variáveis pós-loop
        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]
        
        dados_presentes = (ucc != "" and uff != "" and uh2h != "")

        # --- PROCESSAMENTO LOGICO DAS DUAS TRAVAS DE FERRO ---
        trava_1x = ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_presentes
        trava_x2 = uff in ["V", "E"] and ucc in ["D", "E"] and uh2h in ["D", "E"] and dados_presentes

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: 1X")
        print(f"   [PASSO 1] Casa em Casa ({ucc if ucc else 'VAZIO'})")
        print(f"   [PASSO 2] Fora Fora    ({uff if uff else 'VAZIO'})")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h if uh2h else 'VAZIO'})")
        print(f"   ➔ RESULTADO 1X: {'🟩 GREEN LIGHT (Aprovado)' if trava_1x else '🟥 BLOQUEADO'}")
        print("="*75)

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: X2")
        print(f"   [PASSO 1] Fora Fora    ({uff if uff else 'VAZIO'})")
        print(f"   [PASSO 2] Casa em Casa ({ucc if ucc else 'VAZIO'})")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h if uh2h else 'VAZIO'})")
        print(f"   ➔ RESULTADO X2: {'🟩 GREEN LIGHT (Aprovado)' if trava_x2 else '🟥 BLOQUEADO'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_trava_dupla_chance()
