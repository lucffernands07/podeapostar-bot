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
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def calcular_chance_gols(n1, n2):
    if n1 == 5 and n2 == 5: return "100%"
    if (n1 == 5 and n2 == 4) or (n1 == 4 and n2 == 5): return "85%"
    if n1 == 4 and n2 == 4: return "70%"
    return None

def analisar_detalhes_h2h(driver, url_jogo):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    data = {"c_15": 0, "c_25": 0, "c_h": [], "f_15": 0, "f_25": 0, "f_h": []}
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for i, secao in enumerate(secoes[:2]):
            pref = "c" if i == 0 else "f"
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                res_txt = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "").split("-")
                icon_title = linha.find_element(By.CSS_SELECTOR, ".wcl-icon-rect_At-43").get_attribute("title")
                if "Vitória" in icon_title: data[f"{pref}_h"].append("V")
                elif "Empate" in icon_title: data[f"{pref}_h"].append("E")
                else: data[f"{pref}_h"].append("D")
                gols = [int(g) for g in res_txt if g.isdigit()]
                if sum(gols) > 1.5: data[f"{pref}_15"] += 1
                if sum(gols) > 2.5: data[f"{pref}_25"] += 1
    except: pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return data

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    bilhete = []

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            for el in elementos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_utc = tempo_raw.split()[-1]
                    h_obj = datetime.strptime(h_utc, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    if not ((amanha_no_site in tempo_raw and h_obj.hour <= 3) or ("." not in tempo_raw and (h_obj - timedelta(hours=3)).hour >= 11)): continue

                    id_jogo = el.get_attribute("id").split("_")[-1]
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    t1, t2 = times[0].text.strip(), times[1].text.strip()
                    
                    st = analisar_detalhes_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")
                    mercado = None

                    # Regra Gols
                    ch25 = calcular_chance_gols(st["c_25"], st["f_25"])
                    ch15 = calcular_chance_gols(st["c_15"], st["f_15"])
                    if ch25: mercado = f"Gols +2.5 (Chance {ch25})"
                    elif ch15: mercado = f"Gols +1.5 (Chance {ch15})"
                    
                    # Regra 1X
                    elif st["c_h"].count("D") <= 1 and st["c_h"][0] == "V" and st["f_h"].count("D") >= 2 and st["f_h"][0] == "D":
                        perc = ((5 - st["c_h"].count("D")) / 5) * 100
                        mercado = f"1X (Confiança {int(perc)}%)"
                    
                    # Regra 2X
                    elif st["f_h"].count("D") == 0 and st["c_h"].count("D") >= 2 and st["c_h"][0] == "D":
                        mercado = "2X (Confiança 100%)"

                    if mercado: bilhete.append(f"🏟 *{t1} x {t2}* (`{h_br}`)\n🎯 {mercado}")
                except: continue

        if bilhete: enviar_telegram("📝 *BILHETE GERADO*\n\n" + "\n\n".join(bilhete))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
