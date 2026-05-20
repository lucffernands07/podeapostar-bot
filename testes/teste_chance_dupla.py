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

# Ajuste para importar módulos da pasta raiz (caso precise futuramente)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

def testar_trava_dupla_chance():
    # 📝 LINK CONFIGURADO COM O SEU JOGO DE TESTE (X2)
    url_teste = "https://www.flashscore.com.br/jogo/WjJkJilj/#/h2h/overall"
    t1_nome, t2_nome = "Al-Hazm", "Al-Taawon"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando Teste de Dupla Chance: {t1_nome} x {t2_nome}")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        # Estrutura para espelhar a lógica do seu main
        stats = {
            "t1_resultado_1": "",  # Último jogo em casa do Casa
            "t2_resultado_1": "",  # Último jogo fora do Fora
            "h2h_res_1": ""        # Último H2H na casa do Casa
        }

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # LOOP PELAS 3 SEÇÕES (0: Casa, 1: Fora, 2: H2H)
        for idx, secao in enumerate(secoes[:3]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")
            if not linhas: continue
            
            linha = linhas[0] # Precisamos apenas do ÚLTIMO (L1) para a trava de ferro
            
            try:
                n_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                n_fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                numeros = re.findall(r'\d+', res_texto)
                if len(numeros) < 2: continue
                g1, g2 = int(numeros[0]), int(numeros[1])
                
                # --- PROCESSA SEÇÃO 0: CASA EM CASA ---
                if idx == 0:
                    res_atual = "E"
                    if g1 > g2: res_atual = "V"
                    elif g1 < g2: res_atual = "D"
                    stats["t1_resultado_1"] = res_atual
                    print(f"📊 [CASA] Último em Casa: {n_casa} {g1}-{g2} {n_fora} ➔ Mapeado: {res_atual}")
                
                # --- PROCESSA SEÇÃO 1: FORA FORA ---
                elif idx == 1:
                    res_atual = "E"
                    # Visão sob a ótica do time de fora (t2_nome)
                    if (t2_nome.lower() in n_casa.lower() and g1 > g2) or (t2_nome.lower() in n_fora.lower() and g2 > g1):
                        res_atual = "V"
                    elif (t2_nome.lower() in n_casa.lower() and g1 < g2) or (t2_nome.lower() in n_fora.lower() and g2 < g1):
                        res_atual = "D"
                    stats["t2_resultado_1"] = res_atual
                    print(f"📊 [FORA] Último Fora: {n_casa} {g1}-{g2} {n_fora} ➔ Mapeado (para o Fora): {res_atual}")
                
                # --- PROCESSA SEÇÃO 2: H2H NA CASA ---
                elif idx == 2:
                    res_h2h = "E"
                    # Visão sob a ótica do time da casa (t1_nome)
                    if (t1_nome.lower() in n_casa.lower() and g1 > g2) or (t1_nome.lower() in n_fora.lower() and g2 > g1):
                        res_h2h = "V"
                    elif (t1_nome.lower() in n_casa.lower() and g1 < g2) or (t1_nome.lower() in n_fora.lower() and g2 < g1):
                        res_h2h = "D"
                    stats["h2h_res_1"] = res_h2h
                    print(f"📊 [H2H] Último Confronto: {n_casa} {g1}-{g2} {n_fora} ➔ Mapeado (para o Casa): {res_h2h}")
                    
            except Exception as e:
                print(f"⚠️ Erro na captura da seção {idx}: {e}")

        # Recorta os dados salvos para os testes lógicos
        ucc = stats["t1_resultado_1"]
        uff = stats["t2_resultado_1"]
        uh2h = stats["h2h_res_1"]

        # =========================================================================
        # 🧪 APLICAÇÃO DA TRAVA DE FERRO: 1X
        # =========================================================================
        c1_1x = ucc in ["V", "E"]
        c2_1x = uff in ["D", "E"] # Fora empatou ou perdeu
        c3_1x = uh2h in ["V", "E"]
        trava_1x = c1_1x and c2_1x and c3_1x

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: 1X")
        print(f"   [PASSO 1] Casa em Casa ({ucc}) ➔ {'✅ OK' if c1_1x else '❌ FALHOU (Exige V ou E)'}")
        print(f"   [PASSO 2] Fora Fora    ({uff}) ➔ {'✅ OK' if c2_1x else '❌ FALHOU (Exige D ou E)'}")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h}) ➔ {'✅ OK' if c3_1x else '❌ FALHOU (Exige V ou E)'}")
        print(f"   ➔ RESULTADO 1X: {'🟩 GREEN LIGHT (Aprovado)' if trava_1x else '🟥 BLOQUEADO'}")
        print("="*75)

        # =========================================================================
        # 🧪 APLICAÇÃO DA TRAVA DE FERRO: X2 (Lógica Espelhada)
        # =========================================================================
        c1_x2 = uff in ["V", "E"]  # Fora ganhou ou empatou jogando fora
        c2_x2 = ucc in ["D", "E"]  # Casa perdeu ou empatou jogando em casa
        c3_x2 = uh2h in ["D", "E"] # No H2H o Casa perdeu ou empatou (ou seja, Fora pontuou)
        trava_x2 = c1_x2 and c2_x2 and c3_x2

        print("\n" + "="*75)
        print(f"🔬 AUDITORIA DA TRAVA DE FERRO - MERCADO: X2")
        print(f"   [PASSO 1] Fora Fora    ({uff}) ➔ {'✅ OK' if c1_x2 else '❌ FALHOU (Exige V ou E)'}")
        print(f"   [PASSO 2] Casa em Casa ({ucc}) ➔ {'✅ OK' if c2_x2 else '❌ FALHOU (Exige D ou E)'}")
        print(f"   [PASSO 3] H2H na Casa  ({uh2h}) ➔ {'✅ OK' if c3_x2 else '❌ FALHOU (Exige D ou E do ponto de vista do Casa)'}")
        print(f"   ➔ RESULTADO X2: {'🟩 GREEN LIGHT (Aprovado)' if trava_x2 else '🟥 BLOQUEADO'}")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro durante a varredura: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_trava_dupla_chance()
                    
