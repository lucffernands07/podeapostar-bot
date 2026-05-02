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
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa
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
    options.add_argument("--headless=new") # Versão mais rápida do headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") # Desliga processamento gráfico
    options.add_argument("--blink-settings=imagesEnabled=false") # Não carrega imagens (ganha muita velocidade)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # Define um tempo máximo de espera para o site carregar
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

    
def pegar_estatisticas_h2h(driver, url_jogo, t1, t2):
    # Navegação inicial
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_45_under": 0, "fora_btts": 0, 
        "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", # Novos campos para Vitória Casa
        "pular_gols": False 
    }
    
    try:
        wait = WebDriverWait(driver, 15)
        h2h_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:3]): 
            if idx == 2: 
                try:
                    seletor_btn = "span[data-testid='wcl-scores-caption-05']"
                    botao_mais = secao.find_element(By.CSS_SELECTOR, seletor_btn)
                    driver.execute_script("arguments[0].click();", botao_mais)
                    WebDriverWait(secao, 6).until(lambda s: len(s.find_elements(By.CSS_SELECTOR, ".h2h__row")) >= 6)
                except: pass 

            limite = 6 if idx == 2 else 5
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:limite] 
            
            for i, linha in enumerate(linhas):
                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                    
                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    total = g1 + g2

                    if idx < 2: # --- JOGOS INDIVIDUAIS (CASA/FORA) ---
                        prefixo = "casa" if idx == 0 else "fora"
                        t_ref = t1 if idx == 0 else t2
                        
                        # NOVO: Salva soma de gols do último jogo para a Regra 3/5
                        if i == 0:
                            stats[f"ultimo_gols_{prefixo}"] = total
                        
                        if total > 1.5: stats[f"{prefixo}_15"] += 1
                        if total > 2.5: stats[f"{prefixo}_25"] += 1
                        if total <= 4: stats[f"{prefixo}_45_under"] += 1 # Ajustado nome da chave
                        if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1
                        
                        # Determina resultado V/E/D
                        res_atual = "E"
                        if (t_ref.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t_ref.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_atual = "V"
                            stats[f"{prefixo}_vitorias_recente"] += 1
                        elif (t_ref.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t_ref.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_atual = "D"
                        
                        # Salva o último resultado para o filtro de Vitória Casa
                        if i == 0:
                            stats[f"t{idx+1}_resultado_1"] = res_atual

                    elif idx == 2: # --- CONFRONTO DIRETO (H2H) ---
                        stats["h2h_jogos"] += 1
                        res_h2h = "E"
                        
                        if (t1.lower() in n_casa_h2h.lower() and g1 > g2) or \
                           (t1.lower() in n_fora_h2h.lower() and g2 > g1):
                            res_h2h = "V"
                            stats["h2h_vitorias_t1"] += 1
                        elif (t1.lower() in n_casa_h2h.lower() and g1 < g2) or \
                             (t1.lower() in n_fora_h2h.lower() and g2 < g1):
                            res_h2h = "D"
                            stats["h2h_vitorias_t2"] += 1 # Mantendo contagem original
                        
                        # NOVO: Salva os dois últimos resultados entre eles
                        if i == 0: stats["h2h_res_1"] = res_h2h
                        if i == 1: stats["h2h_res_2"] = res_h2h
                        if g1 == g2: stats["h2h_empates"] += 1 # Mantendo contagem original

                except: continue

        # --- CAPTURA DO LINK BETANO ---
        print(f"      🔗 Buscando link Betano para {t1} x {t2}...")
        stats["link_betano"] = links.extrair_url_betano(driver)

    except Exception as e:
        print(f"      ⚠️ Erro H2H {t1}x{t2}: {e}")
        
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
        # LOOP DE COMPETIÇÕES
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
                        res_vc = vitoria_casa.verificar_vitoria_casa(s)

                        sugestoes_stat = (res_gols + ([f"Ambas Marcam: Sim ({res_btts})"] if res_btts else []) + res_cd + res_vc)[:5]
                        
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
                                elif "Vitória Casa" in m: valor_odd_str = v_odds.get("VITORIA_CASA", "N/A")

                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    if "-4.5" in m and odd_float >= 4.0:
                                        continue 
                                    if odd_float >= 1.25:
                                        lista_para_filtros.append({
                                            "horario": h_br, "time_casa": t1, "time_fora": t2,
                                            "mercado": m, "odd": valor_odd_str, "liga": nome_comp,
                                            "link_betano": s.get("link_betano")
                                        })
                                        total_mercados += 1
                                except: pass
                except: continue

        # --- PROCESSAMENTO E ENVIO FINAL ---
        if lista_para_filtros:
            lista_para_filtros.sort(key=lambda x: (x['horario'], x['liga']))
            
            # 1. Montagem do LISTÃO GERAL (Texto simples para conferência)
            itens_listao = []
            for j in lista_para_filtros:
                itens_listao.append(f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}")
            
            texto_listao_final = "🎫 *LISTA DE MERCADOS DO DIA*\n\n" + "\n\n------------------------------------\n\n".join(itens_listao)
            
            # 2. Montagem dos BINGOS (Estratégicos: 3, 5 e 7)
            novos_bilhetes = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            cache_links = {f"{j['time_casa']}x{j['time_fora']}": j.get("link_betano") for j in lista_para_filtros if j.get("link_betano")}
            texto_bingos_final = bingo357.formatar_para_telegram(novos_bilhetes, cache_links)

            # --- IDENTIFICAÇÃO DE DESTINOS ---
            meu_chat_id = os.getenv('CHAT_ID')     # Seu pessoal
            canal_id = os.getenv('CHANNEL_ID')     # O Canal

            # ENVIO 1: Listão Geral APENAS para você
            if meu_chat_id:
                enviar_telegram(texto_listao_final, meu_chat_id)
                print("📨 Listão enviado para o pessoal.")
            
            # ENVIO 2: Bingos APENAS para o Canal
            if texto_bingos_final and canal_id:
                msg_bingo_formatada = "💰 *SUGESTÕES DE INVESTIMENTO*\n\n" + texto_bingos_final
                enviar_telegram(msg_bingo_formatada, canal_id)
                print("📢 Bingos enviados para o canal.")

            print("✅ Processamento e envios concluídos.")
        else:
            print("⚠️ Nenhuma partida encontrada nos filtros.")


    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
                                    

if __name__ == "__main__":
    main()
