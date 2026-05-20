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

# Função agressiva para limpar qualquer variação de escrita do Flashscore
def normalizar(texto):
    return re.sub(r'[^a-zA-Z0-9]', '', texto.lower().strip())

def testar_nova_logica_posicional():
    url_teste = "https://www.flashscore.com.br/jogo/futebol/al-hazm-YZFeqj3D/al-taawon-WjJkJilj/h2h/total/"
    t1, t2 = "Al Hazm", "Al-Taawon"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando Varredura Posicional Estrita: {t1} x {t2}")
    print(f"🔗 Link: {url_teste}")
    
    # "al hazm" vira "alhazm" | "al-taawon" vira "altaawon"
    t1_alvo = normalizar(t1)
    t2_alvo = normalizar(t2)
    
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
        print(f"📦 Blocos H2H detectados na página: {len(secoes)}")
        
        for idx, secao in enumerate(secoes[:3]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")
            if not linhas: continue
            
            # -----------------------------------------------------------------
            # TABELA 1 (idx == 0): ÚLTIMOS JOGOS DO TIME DA CASA (Al Hazm)
            # -----------------------------------------------------------------
            if idx == 0:
                print("🔎 Analisando Tabela 1 (Últimos jogos do Casa)...")
                for i, linha in enumerate(linhas):
                    el_cima = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                    el_baixo = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                    
                    n_cima_norm = normalizar(el_cima.text)
                    
                    # Debug temporário para ver exatamente o que o robô está comparando na Tabela 1
                    print(f"   [Linha {i+1}] Comparando se alvo '{t1_alvo}' está em '{n_cima_norm}' ({el_cima.text})")
                    
                    if t1_alvo in n_cima_norm:
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        stats["t1_resultado_1"] = res
                        print(f"   🏠 [TABELA 1 - MATCH] Linha {i+1}: {el_cima.text.strip()} {g1}-{g2} {el_baixo.text.strip()} ➔ Letra: {res}")
                        break

            # -----------------------------------------------------------------
            # TABELA 2 (idx == 1): ÚLTIMOS JOGOS DO TIME DE FORA (Al-Taawon)
            # -----------------------------------------------------------------
            elif idx == 1:
                print("🔎 Analisando Tabela 2 (Últimos jogos do Fora)...")
                for i, linha in enumerate(linhas):
                    el_cima = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                    el_baixo = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                    
                    n_baixo_norm = normalizar(el_baixo.text)
                    
                    if t2_alvo in n_baixo_norm:
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g2 > g1 else ("D" if g2 < g1 else "E")
                        stats["t2_resultado_1"] = res
                        print(f"   🚀 [TABELA 2 - MATCH] Linha {i+1}: {el_cima.text.strip()} {g1}-{g2} {el_baixo.text.strip()} ➔ Letra: {res}")
                        break

            # -----------------------------------------------------------------
            # TABELA 3 (idx == 2): CONFRONTOS DIRETOS (H2H HISTÓRICO)
            # -----------------------------------------------------------------
            elif idx == 2:
                print("🔎 Analisando Tabela 3 (Confrontos Diretos)...")
                for i, Secret do H2H in enumerate(linhas):
                    el_cima = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                    el_baixo = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                    
                    n_cima_norm = normalizar(el_cima.text)
                    
                    if t1_alvo in n_cima_norm:
                        gols_el = linha.find_elements(By.CSS_SELECTOR, ".h2h__result span")
                        if len(gols_el) < 2: continue
                        g1, g2 = int(gols_el[0].text.strip()), int(gols_el[1].text.strip())
                        
                        res = "V" if g1 > g2 else ("D" if g1 < g2 else "E")
                        stats["h2h_res_1"] = res
                        print(f"   ⚔️ [TABELA 3 - MATCH] Linha {i+1}: {el_cima.text.strip()} {g1}-{g2} {el_baixo.text.strip()} ➔ Letra: {res}")
                        break

        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]
        dados_ok = (ucc != "" and uff != "" and uh2h != "")

        trava_1x = ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_ok

        print("\n" + "="*75)
        print(f"🔬 CONSOLIDADO DA NOVA REGRA DE DUPLA CHANCE")
        print(f"   [TABELA 1] Último Casa em Casa   ➔ Letra: ({ucc if ucc else 'NULO'})")
        print(f"   [TABELA 2] Último Fora Fora     ➔ Letra: ({uff if uff else 'NULO'})")
        print(f"   [TABELA 3] Último H2H Mando Casa ➔ Letra: ({uh2h if uh2h else 'NULO'})")
        print(f"   ➔ TRAVA DE FERRO 1X: {'🟩 APROVADO (GREEN LIGHT)' if trava_1x else '🟥 BLOQUEADO'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_nova_logica_posicional()
                
