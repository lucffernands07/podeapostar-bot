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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def testar_trava_dupla_chance():
    # ID e nomes corrigidos para o teste do jogo Al-Hazm x Al-Taawon
    id_jogo = "YZFeqj3D" 
    t1, t2 = "Al Hazm", "Al-Taawon"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando Teste Baseado em Seletores de Mando: {t1} x {t2}")
    
    try:
        driver.get(f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")
        wait = WebDriverWait(driver, 15)
        time.sleep(4)
        
        stats = {
            "t1_resultado_1": "", # Último jogo do Al Hazm EM CASA
            "t2_resultado_1": "", # Último jogo do Al-Taawon FORA
            "h2h_res_1": ""        # Último H2H com mando do Al Hazm
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # ---------------------------------------------------------------------
        # SEÇÃO 0: ÚLTIMOS JOGOS DO TIME DA CASA (Al Hazm)
        # ---------------------------------------------------------------------
        if len(secoes) > 0:
            linhas = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                # Localiza mandante e visitante usando as classes da estrutura
                casa_el = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                fora_el = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                
                n_casa = casa_el.text.strip()
                n_fora = fora_el.text.strip()
                
                # Regra: Queremos o primeiro jogo onde o Al Hazm jogou de fato EM CASA (Mandante)
                if t1.lower() in n_casa.lower():
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.strip()
                    gols = re.findall(r'\d+', res_texto)
                    if len(gols) < 2: continue
                    g1, g2 = int(gols[0]), int(gols[1])
                    
                    if g1 > g2: stats["t1_resultado_1"] = "V"
                    elif g1 < g2: stats["t1_resultado_1"] = "D"
                    else: stats["t1_resultado_1"] = "E"
                    
                    print(f"   🏠 [PASSO 1] Confirmado jogo em CASA do {t1}: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {stats['t1_resultado_1']}")
                    break

        # ---------------------------------------------------------------------
        # SEÇÃO 1: ÚLTIMOS JOGOS DO TIME DE FORA (Al-Taawon)
        # ---------------------------------------------------------------------
        if len(secoes) > 1:
            linhas = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                casa_el = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                fora_el = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                
                n_casa = casa_el.text.strip()
                n_fora = fora_el.text.strip()
                
                # Regra: Queremos o primeiro jogo onde o Al-Taawon jogou de fato FORA (Visitante)
                if t2.lower() in n_fora.lower():
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.strip()
                    gols = re.findall(r'\d+', res_texto)
                    if len(gols) < 2: continue
                    g1, g2 = int(gols[0]), int(gols[1])
                    
                    if g2 > g1: stats["t2_resultado_1"] = "V"
                    elif g2 < g1: stats["t2_resultado_1"] = "D"
                    else: stats["t2_resultado_1"] = "E"
                    
                    print(f"   🚀 [PASSO 2] Confirmado jogo FORA do {t2}: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {stats['t2_resultado_1']}")
                    break

        # ---------------------------------------------------------------------
        # SEÇÃO 2: CONFRONTOS DIRETOS (H2H)
        # ---------------------------------------------------------------------
        if len(secoes) > 2:
            linhas = secoes[2].find_elements(By.CSS_SELECTOR, ".h2h__row")
            for linha in linhas:
                casa_el = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant")
                fora_el = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant")
                
                n_casa = casa_el.text.strip()
                n_fora = fora_el.text.strip()
                
                # Regra: H2H com mando do time de casa principal (Al Hazm como mandante)
                if t1.lower() in n_casa.lower():
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.strip()
                    gols = re.findall(r'\d+', res_texto)
                    if len(gols) < 2: continue
                    g1, g2 = int(gols[0]), int(gols[1])
                    
                    if g1 > g2: stats["h2h_res_1"] = "V"
                    elif g1 < g2: stats["h2h_res_1"] = "D"
                    else: stats["h2h_res_1"] = "E"
                    
                    print(f"   ⚔️ [PASSO 3] Confirmado H2H com mando do {t1}: {n_casa} {g1}-{g2} {n_fora} ➔ Letra: {stats['h2h_res_1']}")
                    break

        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]
        
        dados_ok = (ucc != "" and uff != "" and uh2h != "")

        # --- PROCESSAMENTO LOGICO DAS TRAVAS ---
        trava_1x = ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_ok
        trava_x2 = uff in ["V", "E"] and ucc in ["D", "E"] and uh2h in ["D", "E"] and dados_ok

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: 1X")
        print(f"   [PASSO 1] Casa em Casa ({ucc if ucc else 'NULO'})")
        print(f"   [PASSO 2] Fora Fora    ({uff if uff else 'NULO'})")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h if uh2h else 'NULO'})")
        print(f"   ➔ RESULTADO 1X: {'🟩 GREEN LIGHT (Aprovado)' if trava_1x else '🟥 BLOQUEADO'}")
        print("="*75)

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: X2")
        print(f"   [PASSO 1] Fora Fora    ({uff if uff else 'NULO'})")
        print(f"   [PASSO 2] Casa em Casa ({ucc if ucc else 'NULO'})")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h if uh2h else 'NULO'})")
        print(f"   ➔ RESULTADO X2: {'🟩 GREEN LIGHT (Aprovado)' if trava_x2 else '🟥 BLOQUEADO'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_trava_dupla_chance()
            
