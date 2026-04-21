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

# Importação dos seus módulos
from ligas import COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla

def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    if not token or not chat_id:
        print("⚠️ ALERTA: Sem variáveis de ambiente para o Telegram.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id, 
            "text": mensagem, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
        print("🚀 Bilhete enviado!")
    except Exception as e:
        print(f"❌ Falha no Telegram: {e}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "casa_15": 0, "casa_25": 0, "casa_btts": 0, "casa_ult_btts": False, "casa_derrotas": 0, "casa_ult_res": "",
        "casa_ult_15": False, "casa_ult_sofreu": False,
        "fora_15": 0, "fora_25": 0, "fora_btts": 0, "fora_ult_btts": False, "fora_derrotas": 0, "fora_ult_res": "",
        "fora_ult_15": False, "fora_ult_sofreu": False,
        "ult_jogo_zero": False # Sinalizador seletivo para o mercado de gols
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(10)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            prefixo = "casa" if idx == 0 else "fora"
            
            print(f"\n      📊 Analisando H2H: {prefixo.upper()}")

            for i, linha in enumerate(linhas):
                texto_linha = linha.text.replace('\n', ' ')
                numeros = re.findall(r'\d+', texto_linha)
                
                if len(nums := [int(n) for n in numeros]) >= 2:
                    g1, g2 = nums[-2], nums[-1]
                    total = g1 + g2
                    
                    if i == 0:
                        # Se houver um 0 no placar do último jogo de QUALQUER um, sinaliza para o filtro de gols
                        if g1 == 0 or g2 == 0:
                            stats["ult_jogo_zero"] = True
                            print(f"        🔍 Clean Sheet detectado ({g1}x{g2}) - Sinalizando para filtro de gols.")
                        
                        stats[f"{prefixo}_ult_15"] = (total > 1.5)
                        if g1 > 0 and g2 > 0:
                            stats[f"{prefixo}_ult_btts"] = True

                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1

                try:
                    res_el = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip().upper()
                    if i == 0: stats[f"{prefixo}_ult_res"] = res_el
                    if res_el == "D": stats[f"{prefixo}_derrotas"] += 1
                except: pass

    except Exception as e:
        print(f"      Err H2H: {e}")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats


def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    bilhete_agrupado = []
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 10: break
            
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            time.sleep(8)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")

            jogos_do_campeonato = []
            
            for el in elementos:
                if total_mercados >= 10: break
                
                try:
                    tempo_raw = el.find_element(By.CSS_SELECTOR, ".event__time").text.strip()
                    h_obj = datetime.strptime(tempo_raw.split()[-1], "%H:%M")
                    h_br = (h_obj - timedelta(hours=3)).strftime("%H:%M")
                    
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        
                        # Coleta estatísticas (Sua função def atualizada)
                        s = pegar_estatisticas_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall", t1, t2)
                        
                        # Chamada individual dos módulos para evitar erros de lista
                        res_gols = gols.verificar_gols(s)
                        res_btts = ambos_marcam.verificar_btts(s)
                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        
                        sugestoes_lista = []

                        # --- LOGICA DE GOLS (Caso Real Madrid e UNAN) ---
                        if res_gols:
                            if not s.get("ult_jogo_zero"):
                                for m in res_gols:
                                    sugestoes_lista.append(f"🔶 {m}")
                            else:
                                print(f"        ⏭️ Mercado de Gols pulado para {t1} x {t2} (Clean Sheet detectado)")

                        # --- LOGICA DE AMBAS MARCAM ---
                        if res_btts:
                            # Adicionamos apenas se não for duplicado
                            sugestoes_lista.append(f"🔶 Ambas Marcam: Sim ({res_btts})")
                        
                        # --- LOGICA DE CHANCE DUPLA (1X / 2X) ---
                        if res_cd:
                            for m in res_cd:
                                sugestoes_lista.append(f"🔶 {m}")
                        
                        # Montagem final do jogo no bilhete
                        if sugestoes_lista:
                            item = f"⏱️ {h_br} | {nome_comp}\n🏟️ {t1} x {t2}\n" + "\n".join(sugestoes_lista)
                            jogos_do_campeonato.append(item)
                            total_mercados += len(sugestoes_lista)
                            print(f"    ✅ Adicionado: {t1} x {t2} ({len(sugestoes_lista)} mercados)")

                except Exception as e:
                    print(f"      ❌ Erro no jogo: {e}")
                    continue
            
            if jogos_do_campeonato:
                bilhete_agrupado.append("\n\n".join(jogos_do_campeonato))

        if bilhete_agrupado:
            cabecalho = f"🎫 *BILHETE GERADO - {hoje_ref.strftime('%d/%m')}*\n\n"
            corpo = "\n\n----------------------------------------------\n\n".join(bilhete_agrupado)
            rodape = f"\n\n---\n💎 Apostar: Betano | Bet365"
            enviar_telegram(cabecalho + corpo + rodape)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
                
