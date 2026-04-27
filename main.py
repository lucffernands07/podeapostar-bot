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
import odds  
import bingo357  
import links

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
        print(f"Erro Telegram: {e}")

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver
    
def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "casa_15": 0, "casa_25": 0, "casa_45": 0, "casa_btts": 0, 
        "casa_ult_btts": False, "casa_derrotas": 0, "casa_vitorias": 0, "casa_empates": 0, "casa_ult_res": "",
        "casa_ult_15": False, "casa_ult_sofreu": False,
        "fora_15": 0, "fora_25": 0, "fora_45": 0, "fora_btts": 0, 
        "fora_ult_btts": False, "fora_derrotas": 0, "fora_vitorias": 0, "fora_empates": 0, "fora_ult_res": "",
        "fora_ult_15": False, "fora_ult_sofreu": False,
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "pular_gols": False 
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(5)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:3]): 
            # --- EXPANSÃO DO H2H PARA 6 JOGOS ---
            if idx == 2: 
                try:
                    seletor_preciso = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao.find_element(By.CSS_SELECTOR, seletor_preciso)
                    
                    driver.execute_script("arguments[0].click();", botao_mais)
                    
                    # TRAVA DE SEGURANÇA: Espera até que a 6ª linha exista no HTML
                    # Isso evita coletar dados enquanto o site ainda está carregando
                    WebDriverWait(secao, 6).until(
                        lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6
                    )
                    print(f"      ✅ H2H expandido: {t1} x {t2} (6 jogos carregados)")
                except:
                    # Se não houver botão ou demorar demais, segue com o que tiver (5 jogos ou menos)
                    pass 

            # Limite definido: 6 para H2H (idx 2) e 5 para Casa/Fora
            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            for i, linha in enumerate(linhas):
                if idx < 2:
                    prefixo = "casa" if idx == 0 else "fora"
                    texto_linha = linha.text.replace('\n', ' ')
                    numeros = re.findall(r'\d+', texto_linha)
                    if len(nums := [int(n) for n in numeros]) >= 2:
                        g1, g2 = nums[-2], nums[-1] 
                        total = g1 + g2
                        if i == 0:
                            stats[f"{prefixo}_ult_15"] = (total > 1.5)
                            stats[f"{prefixo}_ult_sofreu"] = (g2 > 0)
                            if g1 > 0 and g2 > 0: stats[f"{prefixo}_ult_btts"] = True
                        if total > 1.5: stats[f"{prefixo}_15"] += 1
                        if total > 2.5: stats[f"{prefixo}_25"] += 1
                        if total <= 4: stats[f"{prefixo}_45"] += 1 
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1

                    try:
                        res_el = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip().upper()
                        if i == 0: stats[f"{prefixo}_ult_res"] = res_el
                        if res_el == "V": stats[f"{prefixo}_vitorias"] += 1
                        elif res_el == "E": stats[f"{prefixo}_empates"] += 1
                        elif res_el == "D": stats[f"{prefixo}_derrotas"] += 1
                    except: pass
                        
                elif idx == 2: 
                    try:
                        # Busca o ícone de resultado (V, E ou D)
                        icones = linha.find_elements(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                        if icones:
                            res_h2h = icones[0].text.strip().upper()
                            stats["h2h_jogos"] += 1 # Só conta o jogo se achar o resultado
                            
                            if res_h2h == "V": stats["h2h_vitorias_t1"] += 1
                            elif res_h2h == "E": stats["h2h_empates"] += 1
                            elif res_h2h == "D": stats["h2h_vitorias_t2"] += 1
                    except: pass


    except Exception as e:
        print(f"      ⚠️ Erro H2H: {e}")
        
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stats

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []     
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 100: break 
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            time.sleep(4)
            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            
            for el in elementos:
                if total_mercados >= 100: break 
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
                        
                        url_h2h_final = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
                        s = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        
                        res_gols = gols.verificar_gols(s)
                        res_btts = ambos_marcam.verificar_btts(s)
                        res_cd = chance_dupla.verificar_chance_dupla(s)
                        
                        sugestoes_stat = (res_gols + ([f"Ambas Marcam: Sim ({res_btts})"] if res_btts else []) + res_cd)[:5]
                        
                        if sugestoes_stat:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for m in sugestoes_stat:
                                valor_odd_str = "N/A"
                                if "+1.5" in m: valor_odd_str = v_odds.get("GOLS_15", "N/A")
                                elif "+2.5" in m: valor_odd_str = v_odds.get("GOLS_25", "N/A")
                                elif "-4.5" in m: valor_odd_str = v_odds.get("GOLS_M45", "N/A")
                                elif "Ambas" in m: valor_odd_str = v_odds.get("BTTS", "N/A")
                                elif "1X" in m: valor_odd_str = v_odds.get("1X", "N/A")
                                elif "X2" in m or "2X" in m: valor_odd_str = v_odds.get("X2", "N/A")

                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    if "-4.5" in m and odd_float >= 4.0:
                                        print(f"      🚫 Odd suspeita para -4.5 ({odd_float}). Ignorando...")
                                        continue 
                                    if odd_float >= 1.25:
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m, "odd": valor_odd_str, "liga": nome_comp
                                        })
                                        total_mercados += 1
                                except: pass
                except: continue

        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            itens_listao = []
            for j in lista_para_filtros:
                itens_listao.append(f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}")
            
            texto_listao_final = "🎫 *LISTA DE MERCADOS DO DIA*\n\n" + "\n\n------------------------------------\n\n".join(itens_listao)
            
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            cache_links = {}
            texto_estrategico = None
            
            if novos_bilhetes:
                print("\n🔗 Buscando links reais para os Bilhetes Bingo...")
                for b in novos_bilhetes:
                    for j in b['jogos']:
                        chave = f"{j['time_casa']}x{j['time_fora']}"
                        if chave not in cache_links:
                            cache_links[chave] = links.capturar_link_direto(driver, j['time_casa'], j['time_fora'])
                texto_estrategico = bingo357.formatar_para_telegram(novos_bilhetes, cache_links)

            # Aqui você define a lista de IDs (pegando das variáveis do GitHub)
            destinatarios = [os.getenv('CHAT_ID'), os.getenv('CHANNEL_ID')]
            
            for cid in destinatarios:
                if not cid: 
                    continue
                
                # O comando abaixo CHAMA a função do topo e passa o ID da vez (cid)
                enviar_telegram(texto_listao_final, cid)
                
                if texto_estrategico:
                    enviar_telegram("💰 *SUGESTÕES DE INVESTIMENTO*\n\n" + texto_estrategico, cid)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
        
