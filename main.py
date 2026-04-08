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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        for i, secao in enumerate(secoes[:2]):
            pref = "c" if i == 0 else "f"
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for linha in linhas:
                res_txt = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.replace("\n", "").split("-")
                icon_title = linha.find_element(By.CSS_SELECTOR, ".wcl-icon-rect_At-43").get_attribute("title")
                
                # Histórico (V, E, D) - O topo do site entra no índice [0]
                if "Vitória" in icon_title: data[f"{pref}_h"].append("V")
                elif "Empate" in icon_title: data[f"{pref}_h"].append("E")
                else: data[f"{pref}_h"].append("D")
                
                # Gols
                gols = [int(g) for g in res_txt if g.isdigit()]
                if sum(gols) > 1.5: data[f"{pref}_15"] += 1
                if sum(gols) > 2.5: data[f"{pref}_25"] += 1
    except: pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return data

def main():
    driver = configurar_driver()
    pool_jogos = [] 

    try:
        for nome_comp, url in COMPETICOES.items():
            driver.get(url)
            time.sleep(8)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos:
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    id_jogo = el.get_attribute("id").split("_")[-1]
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                    t1, t2 = times[0].text.strip(), times[1].text.strip()
                    
                    st = analisar_detalhes_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall")
                    if not st["c_h"] or not st["f_h"]: continue

                    mercados_encontrados = []
                    
                    # --- REGRA GOLS (Sua lógica exata) ---
                    def calc_perc(n1, n2):
                        if n1 == 5 and n2 == 5: return 100
                        if (n1 == 5 and n2 == 4) or (n1 == 4 and n2 == 5): return 85
                        if n1 == 4 and n2 == 4: return 70
                        return 0

                    p25 = calc_perc(st["c_25"], st["f_25"])
                    if p25 > 0: mercados_encontrados.append({"desc": f"Gols +2.5 (Chance {p25}%)", "p": p25})
                    
                    p15 = calc_perc(st["c_15"], st["f_15"])
                    if p15 > 0: mercados_encontrados.append({"desc": f"Gols +1.5 (Chance {p15}%)", "p": p15})

                    # --- REGRA 1X (Sua lógica exata) ---
                    # Mandante: max 1 derrota, último vitória ([0]). Visitante: min 2 derrotas, último derrota ([0]).
                    if st["c_h"].count("D") <= 1 and st["c_h"][0] == "V" and \
                       st["f_h"].count("D") >= 2 and st["f_h"][0] == "D":
                        p1x = int(((5 - st["c_h"].count("D")) / 5) * 100)
                        mercados_encontrados.append({"desc": f"1X (Confiança {p1x}%)", "p": p1x})

                    # --- REGRA 2X (Sua lógica exata) ---
                    # Visitante: 0 derrotas. Mandante: min 2 derrotas, último derrota ([0]).
                    if st["f_h"].count("D") == 0 and \
                       st["c_h"].count("D") >= 2 and st["c_h"][0] == "D":
                        mercados_encontrados.append({"desc": "2X (Confiança 100%)", "p": 100})

                    if mercados_encontrados:
                        # Pega os 3 melhores do jogo
                        mercados_encontrados = sorted(mercados_encontrados, key=lambda x: x['p'], reverse=True)[:3]
                        pool_jogos.append({
                            "camp": nome_comp,
                            "hora": tempo_raw,
                            "confronto": f"{t1} x {t2}",
                            "mercados": mercados_encontrados,
                            "max_p": mercados_encontrados[0]['p']
                        })
                except: continue

        if pool_jogos:
            # Seleção dos 13 melhores mercados globais
            pool_jogos.sort(key=lambda x: x['max_p'], reverse=True)
            selecionados = []
            total = 0
            for j in pool_jogos:
                if total >= 13: break
                vagas = 13 - total
                mercados = j['mercados'][:vagas]
                selecionados.append({"camp": j['camp'], "hora": j['hora'], "confronto": j['confronto'], "mercados": mercados})
                total += len(mercados)

            # Ordenação para o Bilhete
            selecionados.sort(key=lambda x: (x['camp'], x['hora']))
            
            msg = "📝 *BILHETE GERADO*\n"
            camp_atual = ""
            for jogo in selecionados:
                if jogo['camp'] != camp_atual:
                    camp_atual = jogo['camp']
                    msg += f"\n🏆 *{camp_atual.upper()}*\n"
                msg += f"\n*{jogo['confronto']}*\n⏱️ {jogo['hora']} | {jogo['camp']}\n"
                for m in jogo['mercados']: msg += f"🎯 {m['desc']}\n"
            
            enviar_telegram(msg)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
