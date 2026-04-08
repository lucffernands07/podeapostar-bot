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

def pegar_estatisticas_h2h(driver, url_jogo):
    """Entra no jogo e analisa os últimos 5 jogos de cada time"""
    # Abre o link do jogo em uma nova aba para não perder a lista principal
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {"casa_15": 0, "casa_25": 0, "fora_15": 0, "fora_25": 0}
    
    try:
        # Clica na aba H2H
        h2h_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(3)

        # Analisa as seções (Casa e Fora)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]): # Apenas os últimos jogos de Casa e Fora
            resultados = secao.find_elements(By.CSS_SELECTOR, ".h2h__result")[:5]
            for res in resultados:
                gols = [int(g) for g in res.text.split("\n")[0].split("-") if g.isdigit()]
                total = sum(gols)
                prefixo = "casa" if idx == 0 else "fora"
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
    
    bilhete = []
    total_jogos_25 = 0

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)
            
            # Captura os IDs dos jogos para construir o link direto
            elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos_jogos:
                try:
                    # Aplica a sua Trava UTC 3h antes de analisar
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    horario_utc = tempo_raw.split()[-1]
                    h_obj = datetime.strptime(horario_utc, "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 11: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        
                        # Pega o ID do jogo para o link
                        id_jogo = el.get_attribute("id").split("_")[-1]
                        link_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        
                        # ANALISA MERCADOS
                        s = pegar_estatisticas_h2h(driver, link_jogo)
                        
                        # REGRA DOS 5 JOGOS (Filtro 5/5 ou 4/5)
                        # Verifica se ambos times batem a média de gols
                        if s["casa_15"] >= 4 and s["fora_15"] >= 4:
                            mercado = "+1.5 Gols"
                            # Se for 5/5 e ainda não temos jogo 2.5, promovemos um
                            if s["casa_25"] >= 4 and s["fora_25"] >= 4 and total_jogos_25 < 1:
                                mercado = "+2.5 Gols"
                                total_jogos_25 += 1
                            
                            bilhete.append(f"✅ `{h_br}` | {t1} x {t2}\n🎯 *Mercado:* {mercado}\n📊 (Casa: {s['casa_15']}/5 | Fora: {s['fora_15']}/5)")

                except: continue

        # ENVIO DO BILHETE FINAL
        if bilhete:
            msg = f"📝 *BILHETE GERADO - {hoje_ref.strftime('%d/%m')}*\n\n"
            msg += "\n\n".join(bilhete)
            msg += f"\n\n⚠️ _Filtro aplicado: Sucesso min 4/5 nos últimos jogos._"
            enviar_telegram(msg)
        else:
            print("Nenhum jogo passou nos critérios técnicos de mercado hoje.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
