import os
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def calcular_chance_gols(c15, f15):
    soma = c15 + f15
    if soma == 10: return "100%"
    if soma == 9: return "85%"
    if soma == 8: return "70%"
    return None

def pegar_estatisticas_h2h(driver, url_jogo):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    stats = {"c15": 0, "c25": 0, "f15": 0, "f25": 0, "cv": 0, "cd": 0, "fv": 0, "fd": 0, "c_hist": [], "f_hist": []}
    
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(3)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for idx, secao in enumerate(secoes[:2]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            prefixo = "c" if idx == 0 else "f"
            for linha in linhas:
                res = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                stats[f"{prefixo}_hist"].append(res)
                if res == "V": stats[f"{prefixo}v"] += 1
                if res == "D": stats[f"{prefixo}d"] += 1
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "-")
                gols = [int(g) for g in placar.split("-") if g.strip().isdigit()]
                total = sum(gols) if gols else 0
                if total > 1.5: stats[f"{prefixo}15"] += 1
                if total > 2.5: stats[f"{prefixo}25"] += 1
    except: pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now() - timedelta(hours=3)
    print(f"Executando bot: {hoje_ref.strftime('%d/%m/%Y %H:%M')}")

    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        
        # ESPERA EXPLÍCITA: Garante que os jogos apareçam antes de tentar ler
        wait_main = WebDriverWait(driver, 20)
        wait_main.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match")))
        time.sleep(5) 
        
        elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        print(f"Encontrados {len(elementos_jogos)} eventos na página. Filtrando agendados...")
        
        for el in elementos_jogos:
            try:
                txt = el.text
                # Filtro: Tem que ter horário (:) e NÃO ter placar (indicando jogo futuro)
                if ":" in txt and not any(s.text.strip() for s in el.find_elements(By.CSS_SELECTOR, ".event__score")):
                    
                    # CAPTURA DIA 08 (Lista Principal)
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    if len(times) < 2: continue
                    
                    t1, t2 = times[0].text.strip(), times[1].text.strip()
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    link_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                    
                    s = pegar_estatisticas_h2h(driver, link_jogo)
                    mercados = []

                    # Gols
                    p15 = calcular_chance_gols(s["c15"], s["f15"])
                    if p15: mercados.append(f"🎯 Gols +1.5 (Chance {p15})")
                    p25 = calcular_chance_gols(s["c25"], s["f25"])
                    if p25: mercados.append(f"🎯 Gols +2.5 (Chance {p25})")

                    # Regras 1X/2X (Índice [-1] mantido)
                    if s["cd"] <= 1 and s["c_hist"][-1] == "V" and s["fd"] >= 2 and s["f_hist"][-1] == "D":
                        mercados.append(f"🎯 Mercado 1X (Ativo)")
                    if s["fd"] == 0 and s["cd"] >= 2 and s["c_hist"][-1] == "D":
                        mercados.append(f"🎯 Mercado 2X (Chance Alta)")

                    if mercados:
                        print(f"\n✅ {t1} x {t2}")
                        for m in mercados: print(m)
            except: continue

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
