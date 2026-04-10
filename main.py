import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from ligas import COMPETICOES
import mercado_gols
import mercado_btts
import mercado_chance_dupla

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={
        "chat_id": chat_id, 
        "text": mensagem, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })

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
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(4)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for idx, secao in enumerate(secoes[:2]):
            resultados = secao.find_elements(By.CSS_SELECTOR, ".h2h__result")[:5]
            prefixo = "casa" if idx == 0 else "fora"
            for res in resultados:
                numeros = re.findall(r'\d+', res.text)
                if len(numeros) >= 2:
                    total = int(numeros[0]) + int(numeros[1])
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
    except: pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    bilhete_agrupado = []

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            jogos_do_campeonato = []
            
            for el in elementos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_obj = datetime.strptime(tempo_raw.split()[-1], "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 11: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        
                        s = pegar_estatisticas_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")
                        
                        # Chamada dos módulos de mercado
                        mercados_bloco = mercado_gols.verificar_gols(s)
                        
                        if mercados_bloco:
                            item = f"⏱️ {h_br} | {nome_comp}\n🏟️ {t1} x {t2}\n" + "\n".join(mercados_bloco)
                            jogos_do_campeonato.append(item)
                except: continue
            
            if jogos_do_campeonato:
                bilhete_agrupado.append("\n\n".join(jogos_do_campeonato))

        if bilhete_agrupado:
            cabecalho = f"🎫 *BILHETE GERADO - {hoje_ref.strftime('%d/%m')}*\n🎯 *MERCADOS: GOLS +1.5 / +2.5 / 1X / 2X*\n\n"
            corpo = "\n\n---\n\n".join(bilhete_agrupado)
            rodape = "\n\n---\n💎 *Apostar:* [Betano](https://br.betano.com/) | [Bet365](https://www.bet365.com/)"
            enviar_telegram(cabecalho + corpo + rodape)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
