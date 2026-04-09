import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/",
    "Europa League": "https://www.flashscore.com.br/futebol/europa/liga-europa/"
}

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def pegar_estatisticas_h2h(driver, url_jogo):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    stats = {"casa_15": 0, "casa_25": 0, "fora_15": 0, "fora_25": 0}
    try:
        h2h_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(3)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for idx, secao in enumerate(secoes[:2]):
            resultados = secao.find_elements(By.CSS_SELECTOR, ".h2h__result")[:5]
            for res in resultados:
                placar_texto = res.text.replace('\n', ' ').split(' ')[0]
                gols = [int(g) for g in placar_texto.split("-") if g.strip().isdigit()]
                total = sum(gols) if gols else 0
                prefixo = "casa" if idx == 0 else "fora"
                if total > 1.5: stats[f"{prefixo}_15"] += 1
                if total > 2.5: stats[f"{prefixo}_25"] += 1
    except: pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    bilhete = []

    try:
        for nome_comp, url in COMPETICOES.items():
            print(f"\n--- Acessando: {nome_comp} ---")
            driver.get(url)
            time.sleep(8)
            elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos_jogos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    horario_utc = tempo_raw.split()[-1]
                    h_obj = datetime.strptime(horario_utc, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    # Log de tempo para sabermos se a trava UTC está aceitando o jogo
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 11: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        print(f"  > Analisando: {t1} x {t2}")
                        
                        id_jogo = el.get_attribute("id").split("_")[-1]
                        link_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        
                        s = pegar_estatisticas_h2h(driver, link_jogo)
                        print(f"    [LOG STATS] Casa: +1.5:{s['casa_15']} +2.5:{s['casa_25']} | Fora: +1.5:{s['fora_15']} +2.5:{s['fora_25']}")
                        
                        ch15 = calcular_chance(s["casa_15"], s["fora_15"])
                        ch25 = calcular_chance(s["casa_25"], s["fora_25"])
                        
                        mercados_jogo = []
                        if ch15: mercados_jogo.append(f"Gols +1.5 (Chance {ch15})")
                        if ch25: mercados_jogo.append(f"Gols +2.5 (Chance {ch25})")
                        
                        if mercados_jogo:
                            msg_jogo = f"✅ `{h_br}` | {t1} x {t2}\n🎯 *Mercado:* {' | '.join(mercados_jogo)}"
                            bilhete.append(msg_jogo)
                            print(f"    !!! JOGO ADICIONADO AO BILHETE !!!")

                except Exception as e:
                    continue

        if not bilhete:
            print("\nResultado Final: Nenhum jogo passou nos critérios técnicos hoje.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
