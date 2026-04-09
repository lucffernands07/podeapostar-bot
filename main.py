import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def calcular_porcentagem_gols(casa_5, fora_5):
    soma = casa_5 + fora_5
    if soma == 10: return "100%"
    if soma == 9: return "85%"
    if soma == 8: return "70%"
    return None

def extrair_dados_h2h(driver, id_jogo):
    url_resumo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/resumo-de-jogo"
    driver.execute_script(f"window.open('{url_resumo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    analise = {"confronto": "", "mercados": []}
    
    try:
        wait = WebDriverWait(driver, 25)
        
        # --- TRAVA ANTI-DUPLICAÇÃO ---
        # Espera até que existam 2 nomes e que o segundo não seja igual ao primeiro
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".participant__participantName")) >= 2)
        
        def nomes_carregados(d):
            n = d.find_elements(By.CSS_SELECTOR, ".participant__participantName")
            return n[0].text.strip() != "" and n[1].text.strip() != "" and n[0].text.strip() != n[1].text.strip()
        
        try:
            wait.until(nomes_carregados)
        except:
            pass # Se estourar o tempo, tenta seguir com o que tem

        nomes = driver.find_elements(By.CSS_SELECTOR, ".participant__participantName")
        t_casa = nomes[0].text.strip()
        t_fora = nomes[1].text.strip()
        analise["confronto"] = f"{t_casa} x {t_fora}"

        # Clique na aba H2H
        aba = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='wcl-tab' and contains(., 'H2H')]")))
        driver.execute_script("arguments[0].click();", aba)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(5) # Tempo para renderizar os ícones

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        stats = []

        for secao in secoes[:2]:
            v, d, g15, g25 = 0, 0, 0, 0
            historico = []
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            
            for linha in linhas:
                res = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                historico.append(res)
                if res == "V": v += 1
                if res == "D": d += 1
                
                placar_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "-")
                # Extração de gols segura
                gols_indices = [int(g) for g in placar_texto.split("-") if g.strip().isdigit()]
                soma = sum(gols_indices) if gols_indices else 0
                
                if soma > 1.5: g15 += 1
                if soma > 2.5: g25 += 1
            
            stats.append({"v": v, "d": d, "g15": g15, "g25": g25, "hist": historico})

        c, f = stats[0], stats[1]

        # REGRAS (Índice [-1] mantido como solicitado)
        p15 = calcular_porcentagem_gols(c["g15"], f["g15"])
        if p15: analise["mercados"].append(f"🎯 Gols +1.5 (Chance {p15})")
        
        p25 = calcular_porcentagem_gols(c["g25"], f["g25"])
        if p25: analise["mercados"].append(f"🎯 Gols +2.5 (Chance {p25})")

        if c["d"] <= 1 and c["hist"][-1] == "V" and f["d"] >= 2 and f["hist"][-1] == "D":
            p_1x = ((5 - c["d"]) + f["d"]) * 10
            analise["mercados"].append(f"🎯 Mercado 1X (Chance {p_1x}%)")

        if f["d"] == 0 and c["d"] >= 2 and c["hist"][-1] == "D":
            analise["mercados"].append(f"🎯 Mercado 2X (Chance Alta)")

    except Exception:
        pass
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return analise

def main():
    driver = configurar_driver()
    agora = datetime.utcnow() - timedelta(hours=3)
    print(f"Executando bot: {agora.strftime('%d/%m/%Y %H:%M')}")

    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(15)
        
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        ids = []
        for el in elementos:
            if ":" in el.text and not any(s.text.strip() for s in el.find_elements(By.CSS_SELECTOR, ".event__score")):
                ids.append(el.get_attribute("id").split("_")[-1])

        print(f"Analisando {len(ids)} jogos agendados...")
        for j_id in ids:
            resultado = extrair_dados_h2h(driver, j_id)
            if resultado["mercados"]:
                print(f"\n✅ {resultado['confronto']}")
                for m in resultado["mercados"]:
                    print(m)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
        
