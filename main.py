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

COMPETICOES = {
    "Champions League": "https://www.flashscore.com.br/futebol/europa/liga-dos-campeoes/",
    "Libertadores": "https://www.flashscore.com.br/futebol/america-do-sul/copa-libertadores/",
    "Sul-Americana": "https://www.flashscore.com.br/futebol/america-do-sul/copa-sul-americana/",
    "Europa League": "https://www.flashscore.com.br/futebol/europa/liga-europa/"
}

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id:
        print("⚠️ ALERTA: Sem TELEGRAM_TOKEN ou CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
        if res.status_code == 200:
            print("🚀 Bilhete enviado com sucesso!")
        else:
            print(f"❌ Erro no envio: {res.text}")
    except Exception as e:
        print(f"❌ Falha de conexão: {e}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def pegar_estatisticas_h2h(driver, url_jogo):
    print(f"    [LINK] {url_jogo}")
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "casa_15": 0, "casa_25": 0, "casa_derrotas": 0, "casa_ult": "",
        "fora_15": 0, "fora_25": 0, "fora_derrotas": 0, "fora_ult": ""
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(4)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            prefixo = "casa" if idx == 0 else "fora"
            
            for i, linha in enumerate(linhas):
                try:
                    res_icon = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                    if i == 0: stats[f"{prefixo}_ult"] = res_icon
                    if res_icon == "D": stats[f"{prefixo}_derrotas"] += 1
                except: pass

                numeros = re.findall(r'\d+', linha.text)
                if len(numeros) >= 2:
                    total = int(numeros[-2]) + int(numeros[-1])
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
    except: pass
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def calcular_chance_gols(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    jogos_bilhete = []

    try:
        for nome_comp, url in COMPETICOES.items():
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            time.sleep(8)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
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
                        print(f"  > Analisando: {t1} x {t2}...")
                        
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        link_analise = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        
                        s = pegar_estatisticas_h2h(driver, link_analise)
                        
                        print(f"    [GOLS] {t1}: {s['casa_15']}/5 | {t2}: {s['fora_15']}/5")
                        print(f"    [RES]  {t1}: {5-s['casa_derrotas']}/5 (Ult:{s['casa_ult']}) | {t2}: {5-s['fora_derrotas']}/5 (Ult:{s['fora_ult']})")
                        
                        mercados_detalhes = []
                        
                        # Gols
                        ch15 = calcular_chance_gols(s["casa_15"], s["fora_15"])
                        ch25 = calcular_chance_gols(s["casa_25"], s["fora_25"])
                        if ch15: mercados_detalhes.append(f"🎯 Mercado: +1.5 Gols ({ch15})")
                        if ch25: mercados_detalhes.append(f"🎯 Mercado: +2.5 Gols ({ch25})")

                        # Dupla Chance
                        if s["casa_derrotas"] <= 1 and s["casa_ult"] == "V" and s["fora_derrotas"] >= 2 and s["fora_ult"] == "D":
                            mercados_detalhes.append("🎯 Mercado: 1x (100%)")
                        
                        if s["fora_derrotas"] == 0 and s["casa_derrotas"] >= 2 and s["casa_ult"] == "D":
                            mercados_detalhes.append("🎯 Mercado: 2x (100%)")

                        if mercados_detalhes:
                            # Formatação individual de cada jogo no novo padrão
                            bloco_jogo = f"⏱️ {h_br} | {nome_comp}\n🏟️ {t1} x {t2}\n" + "\n".join(mercados_detalhes)
                            jogos_bilhete.append(bloco_jogo)
                            print("    !!! ADICIONADO AO BILHETE !!!")
                except: continue

        if jogos_bilhete:
            print("\nFormatando e enviando bilhete...")
            data_formatada = hoje_ref.strftime('%d/%m')
            
            cabecalho = f"🎫 *BILHETE GERADO - {data_formatada}*\n"
            cabecalho += "🎯 *MERCADOS: GOLS +1.5 / +2.5 / 1X / 2X*\n\n"
            
            corpo = "\n\n---\n\n".join(jogos_bilhete)
            
            rodape = "\n\n---\n💎 *Apostar: [Betano](https://www.betano.com) | [Bet365](https://www.bet365.com)*"
            
            enviar_telegram(cabecalho + corpo + rodape)
        else:
            print("\nFim: Nenhum jogo passou.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
