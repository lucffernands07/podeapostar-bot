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

def extrair_dados_h2h(driver, id_jogo, confronto_nome):
    # Técnica do dia 08: Abre direto o H2H sabendo o nome antecipadamente
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    driver.execute_script(f"window.open('{url_h2h}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    analise = {"confronto": confronto_nome, "mercados": []}
    
    try:
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        time.sleep(4)

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
                
                placar_txt = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "-")
                gols_list = [int(g) for g in placar_txt.split("-") if g.strip().isdigit()]
                soma = sum(gols_list) if gols_list else 0
                if soma > 1.5: g15 += 1
                if soma > 2.5: g25 += 1
            
            stats.append({"v": v, "d": d, "g15": g15, "g25": g25, "hist": historico})

        c, f = stats[0], stats[1]

        # REGRAS (Índice [-1] mantido como solicitado)
        p15 = calcular_porcentagem_gols(c["g15"], f["g15"])
        if p15: analise["mercados"].append(f"🎯 Gols +1.5 (Chance {p15})")
        
        p25 = calcular_porcentagem_gols(c["g25"], f["g25"])
        if p25: analise["mercados"].append(f"🎯 Gols +2.5 (Chance {p25})")

        # Regra 1X: mandante max 1D (última V), visitante min 2D (última D)
        if c["d"] <= 1 and c["hist"][-1] == "V" and f["d"] >= 2 and f["hist"][-1] == "D":
            p_1x = ((5 - c["d"]) + f["d"]) * 10
            analise["mercados"].append(f"🎯 Mercado 1X (Chance {p_1x}%)")

        # Regra 2X: visitante 0D, mandante min 2D (última D)
        if f["d"] == 0 and c["d"] >= 2 and c["hist"][-1] == "D":
            analise["mercados"].append(f"🎯 Mercado 2X (Chance Alta)")

    except: pass
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return analise

def main():
    driver = configurar_driver()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    print(f"Executando bot: {agora_br.strftime('%d/%m/%Y %H:%M')}")

    try:
        driver.get("https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/")
        time.sleep(12)
        
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        jogos_para_analisar = []

        # TÉCNICA DO DIA 08: Captura os nomes na LISTA PRINCIPAL
        for el in elementos:
            if ":" in el.text and not any(s.text.strip() for s in el.find_elements(By.CSS_SELECTOR, ".event__score")):
                id_jogo = el.get_attribute("id").split("_")[-1]
                times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                if len(times) >= 2:
                    nome_completo = f"{times[0].text.strip()} x {times[1].text.strip()}"
                    jogos_para_analisar.append({"id": id_jogo, "nome": nome_completo})

        print(f"Analisando {len(jogos_para_analisar)} jogos...")
        for jogo in jogos_para_analisar:
            resultado = extrair_dados_h2h(driver, jogo["id"], jogo["nome"])
            if resultado["mercados"]:
                print(f"\n✅ {resultado['confronto']}")
                for m in resultado["mercados"]:
                    print(m)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
                
