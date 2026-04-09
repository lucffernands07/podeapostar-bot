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

def analisar_h2h(driver, id_jogo, confronto):
    # Igual ao dia 08: Abre o H2H direto
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    driver.execute_script(f"window.open('{url_h2h}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    dados_final = {"confronto": confronto, "mercados": []}
    
    try:
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(4)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        stats_times = []

        for secao in secoes[:2]:
            v, d, g15, g25 = 0, 0, 0, 0
            historico = []
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                res = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                historico.append(res)
                if res == "V": v += 1
                if res == "D": d += 1
                
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "-")
                gols = sum([int(g) for g in placar.split("-") if g.strip().isdigit()])
                if gols > 1.5: g15 += 1
                if gols > 2.5: g25 += 1
            
            stats_times.append({"v": v, "d": d, "g15": g15, "g25": g25, "hist": historico})

        c, f = stats_times[0], stats_times[1]

        # REGRAS DE MERCADO
        p15 = calcular_porcentagem_gols(c["g15"], f["g15"])
        if p15: dados_final["mercados"].append(f"🎯 Gols +1.5 (Chance {p15})")
        
        p25 = calcular_porcentagem_gols(c["g25"], f["g25"])
        if p25: dados_final["mercados"].append(f"🎯 Gols +2.5 (Chance {p25})")

        # 1X: mandante max 1D (última V), visitante min 2D (última D)
        if c["d"] <= 1 and c["hist"][-1] == "V" and f["d"] >= 2 and f["hist"][-1] == "D":
            p_1x = ((5 - c["d"]) + f["d"]) * 10
            dados_final["mercados"].append(f"🎯 Mercado 1X (Chance {p_1x}%)")

        # 2X: visitante 0D, mandante min 2D (última D)
        if f["d"] == 0 and c["d"] >= 2 and c["hist"][-1] == "D":
            dados_final["mercados"].append(f"🎯 Mercado 2X (Chance Alta)")

    except: pass
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return dados_final

def main():
    driver = configurar_driver()
    # Ajuste UTC-3 para pegar jogos até as 03:00 do dia seguinte
    agora_br = datetime.utcnow() - timedelta(hours=3)
    print(f"Executando bot: {agora_br.strftime('%d/%m/%Y %H:%M')}")

    try:
        # Foco na Libertadores
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(15)
        
        jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        
        print(f"Analisando jogos agendados...")
        for jogo in jogos:
            texto = jogo.text
            # Filtra apenas jogos com horário e sem placar
            if ":" in texto and not any(s.text.strip() != "" for s in jogo.find_elements(By.CSS_SELECTOR, ".event__score")):
                id_j = jogo.get_attribute("id").split("_")[-1]
                times = jogo.find_elements(By.CSS_SELECTOR, "span[class*='participant']")
                if len(times) >= 2:
                    conf = f"{times[0].text.strip()} x {times[1].text.strip()}"
                    horario = jogo.find_element(By.CSS_SELECTOR, ".event__time").text
                    
                    res = analisar_h2h(driver, id_j, conf)
                    if res["mercados"]:
                        print(f"\n✅ {horario} | {res['confronto']}")
                        for m in res["mercados"]:
                            print(m)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                
