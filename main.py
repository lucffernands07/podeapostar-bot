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
    return driver

def analisar_detalhes_h2h(driver, url_jogo):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    data = {"c_15": 0, "c_25": 0, "c_h": [], "f_15": 0, "f_25": 0, "f_h": []}
    try:
        # Espera carregar os blocos de H2H
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for i, secao in enumerate(secoes[:2]):
            pref = "c" if i == 0 else "f"
            # Pega as últimas 5 linhas de resultados
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                # CORREÇÃO: Busca o texto 'V', 'E' ou 'D' diretamente no elemento de resultado
                try:
                    res_status = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip()
                    if res_status:
                        data[f"{pref}_h"].append(res_status)
                except: pass

                # Gols (pega o placar ex: 1-2)
                try:
                    res_txt = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "").split("-")
                    gols = [int(g) for g in res_txt if g.strip().isdigit()]
                    if sum(gols) > 1.5: data[f"{pref}_15"] += 1
                    if sum(gols) > 2.5: data[f"{pref}_25"] += 1
                except: pass
    except Exception as e:
        print(f"Erro ao ler H2H: {e}")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return data

def main():
    driver = configurar_driver()
    pool_jogos = [] 

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(10)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos:
                try:
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    t1, t2 = times[0].text.strip(), times[1].text.strip()
                    tempo = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    
                    st = analisar_detalhes_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")
                    
                    # Se não conseguiu ler os resultados (st["c_h"]), pula para não dar erro de índice [0]
                    if not st["c_h"] or not st["f_h"]: continue

                    mercados_jogo = []
                    
                    # --- REGRA GOLS ---
                    def calc_gols(n1, n2):
                        if n1 == 5 and n2 == 5: return 100
                        if (n1 == 5 and n2 == 4) or (n1 == 4 and n2 == 5): return 85
                        if n1 == 4 and n2 == 4: return 70
                        return 0

                    p25 = calc_gols(st["c_25"], st["f_25"])
                    if p25 > 0: mercados_jogo.append({"desc": f"Gols +2.5 (Chance {p25}%)", "p": p25})
                    
                    p15 = calc_gols(st["c_15"], st["f_15"])
                    if p15 > 0: mercados_jogo.append({"desc": f"Gols +1.5 (Chance {p15}%)", "p": p15})

                    # --- REGRA 1X ---
                    if st["c_h"].count("D") <= 1 and st["c_h"][0] == "V" and \
                       st["f_h"].count("D") >= 2 and st["f_h"][0] == "D":
                        p1x = int(((5 - st["c_h"].count("D")) / 5) * 100)
                        mercados_jogo.append({"desc": f"1X (Confiança {p1x}%)", "p": p1x})

                    # --- REGRA 2X ---
                    if st["f_h"].count("D") == 0 and \
                       st["c_h"].count("D") >= 2 and st["c_h"][0] == "D":
                        mercados_jogo.append({"desc": "2X (Confiança 100%)", "p": 100})

                    if mercados_jogo:
                        mercados_jogo = sorted(mercados_jogo, key=lambda x: x['p'], reverse=True)[:3]
                        pool_jogos.append({
                            "camp": nome_comp,
                            "hora": tempo,
                            "confronto": f"{t1} x {t2}",
                            "mercados": mercados_jogo,
                            "max_p": mercados_jogo[0]['p']
                        })
                except: continue

        if pool_jogos:
            pool_jogos.sort(key=lambda x: x['max_p'], reverse=True)
            selecionados = []
            total = 0
            for j in pool_jogos:
                if total >= 13: break
                vagas = 13 - total
                mercs = j['mercados'][:vagas]
                selecionados.append({"camp": j['camp'], "hora": j['hora'], "confronto": j['confronto'], "mercados": mercs})
                total += len(mercs)

            selecionados.sort(key=lambda x: (x['camp'], x['hora']))
            
            msg = "📝 *BILHETE ELITE*\n"
            camp_atual = ""
            for jogo in selecionados:
                if jogo['camp'] != camp_atual:
                    camp_atual = jogo['camp']; msg += f"\n🏆 *{camp_atual.upper()}*\n"
                msg += f"\n*{jogo['confronto']}*\n⏱️ {jogo['hora']}\n"
                for m in jogo['mercados']: msg += f"🎯 {m['desc']}\n"
            enviar_telegram(msg)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
            
