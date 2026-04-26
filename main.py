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
import odds  # Importa o módulo odds.py que você enviou
import tripla_dupla  # Importando o novo arquivo

def enviar_telegram(mensagem, chat_id_destino):
    token = os.getenv('TELEGRAM_TOKEN')
    if not token or not chat_id_destino:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id_destino, 
            "text": mensagem, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"Erro: {e}")

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
        "casa_15": 0, "casa_25": 0, "casa_45": 0, "casa_btts": 0, "casa_ult_btts": False, "casa_derrotas": 0, "casa_ult_res": "",
        "casa_ult_15": False, "casa_ult_sofreu": False,
        "fora_15": 0, "fora_25": 0, "fora_45": 0, "fora_btts": 0, "fora_ult_btts": False, "fora_derrotas": 0, "fora_ult_res": "",
        "fora_ult_15": False, "fora_ult_sofreu": False,
        "pular_gols": False 
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(5)
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
                        if idx == 0 and (total <= 1):
                            stats["pular_gols"] = True
                            print(f"        🚫 Jogo muito seco na CASA ({g1}x{g2}). Travando Over.")
                        
                        stats[f"{prefixo}_ult_15"] = (total > 1.5)
                        stats[f"{prefixo}_ult_sofreu"] = (g2 > 0)

                        if g1 > 0 and g2 > 0:
                            stats[f"{prefixo}_ult_btts"] = True

                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if total <= 4: stats[f"{prefixo}_45"] += 1 
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
    
    bilhete_agrupado_texto = [] # Para o listão do Telegram
    lista_para_filtros = []     # Lista "bruta" para o tripla_dupla.py
    total_mercados = 0 

    try:
        # Loop principal pelas ligas
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 50: break 
            
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            time.sleep(4)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")

            jogos_do_campeonato = []
            
            for el in elementos:
                if total_mercados >= 50: break 
                
                try:
                    # [Lógica de Horário e Filtro de Datas]
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
                        
                        # Extração de Estatísticas e Sugestões
                        url_h2h_final = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        s = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
                        res_gols = gols.verificar_gols(s)
                        res_btts = ambos_marcam.verificar_btts(s)
                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        
                        sugestoes_stat = (res_gols + ([f"Ambas Marcam: Sim ({res_btts})"] if res_btts else []) + res_cd)[:5]
                        
                        if sugestoes_stat:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            sugestoes_com_odd_validada = []

                            for m in sugestoes_stat:
                                # Mapeamento de odds
                                valor_odd_str = "N/A"
                                if "+1.5" in m: valor_odd_str = v_odds.get("GOLS_15", "N/A")
                                elif "+2.5" in m: valor_odd_str = v_odds.get("GOLS_25", "N/A")
                                elif "-4.5" in m: valor_odd_str = v_odds.get("GOLS_M45", "N/A")
                                elif "Ambas" in m: valor_odd_str = v_odds.get("BTTS", "N/A")
                                elif "1X" in m: valor_odd_str = v_odds.get("1X", "N/A")
                                elif "X2" in m or "2X" in m: valor_odd_str = v_odds.get("X2", "N/A")

                                try:
                                    # Filtro de Odd Mínima (1.20)
                                    if float(valor_odd_str.replace(',', '.')) >= 1.20:
                                        sugestoes_com_odd_validada.append(f"🔶 {m} | Odd: `{valor_odd_str}`")
                                        
                                        # Alimenta a lista para o construtor de triplas
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m, "odd": valor_odd_str, "liga": nome_comp
                                        })
                                except: pass

                            if sugestoes_com_odd_validada:
                                item = (f"⏱️ {h_br} | {nome_comp}\n🏟️ {t1} x {t2}\n" + "\n".join(sugestoes_com_odd_validada))
                                jogos_do_campeonato.append(item)
                                total_mercados += len(sugestoes_com_odd_validada)
                except: continue
            
            if jogos_do_campeonato:
                bilhete_agrupado_texto.append("\n\n".join(jogos_do_campeonato))

        # --- SISTEMA DE ENVIO DUPLO ---
        if bilhete_agrupado_texto:
            destinatarios = [os.getenv('CHAT_ID'), "-1003982717570"]
            
            # Formata as mensagens uma única vez para economizar processamento
            texto_listao = "🎫 *LISTA DE MERCADOS DO DIA*\n\n" + "\n\n---\n\n".join(bilhete_agrupado_texto)
            novos_bilhetes = tripla_dupla.montar_bilhetes_estrategicos(lista_para_filtros)
            
            for cid in destinatarios:
                if not cid: continue
                
                # Envia a lista completa de 50 jogos
                enviar_telegram(texto_listao, cid)
                
                # Envia as sugestões de Triplas (se houver)
                if novos_bilhetes:
                    texto_triplas = "💰 *SUGESTÕES DE INVESTIMENTO*\n\n" + tripla_dupla.formatar_para_telegram(novos_bilhetes)
                    enviar_telegram(texto_triplas, cid)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
    
