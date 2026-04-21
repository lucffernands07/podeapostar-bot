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
        "pular_gols": False
    }
    
    try:
        h2h_tab = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/h2h')]")))
        h2h_tab.click()
        time.sleep(10)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        for idx, secao in enumerate(secoes[:2]):
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            prefixo = "casa" if idx == 0 else "fora"
            nosso_time = t1.lower() if idx == 0 else t2.lower()
            
            print(f"\n      📊 Analisando H2H: {nosso_time.upper()}")

            for i, linha in enumerate(linhas):
                try:
                    res_element = linha.find_element(By.CSS_SELECTOR, "span[class*='h2h__icon']").text.strip().upper()
                    if i == 0: stats[f"{prefixo}_ult_res"] = res_element
                    if res_element == "D": stats[f"{prefixo}_derrotas"] += 1
                except: pass

                # --- LOG DE NÚMEROS DA LINHA ---
                texto_linha = linha.text.replace('\n', ' ')
                numeros = re.findall(r'\d+', texto_linha)
                
                if len(nums := [int(n) for n in numeros]) >= 2:
                    # g1 e g2 aqui são os dois últimos números que o re.findall achou
                    g1, g2 = nums[-2], nums[-1]
                    total = g1 + g2
                    
                    # LOG DE VALIDAÇÃO NO CONSOLE
                    log_numeros = " | ".join([f"g{k+1}:{v}" for k, v in enumerate(nums)])
                    print(f"        [Jogo {i+1}] {log_numeros} -> Placar Identificado: {g1}x{g2}")

                    if i == 0:
                        try:
                            # Tenta identificar quem é quem para a sua regra
                            part_casa = linha.find_element(By.CSS_SELECTOR, ".h2h__participant--home").text.strip().lower()
                            
                            if nosso_time in part_casa or part_casa in nosso_time:
                                marcou, sofreu = (g1 > 0), (g2 > 0)
                            else:
                                marcou, sofreu = (g2 > 0), (g1 > 0)

                            if not marcou or not sofreu:
                                stats["pular_gols"] = True
                                print(f"        ⚠️ TRAVA ATIVADA: {nosso_time} (Marcou:{marcou} / Sofreu:{sofreu})")
                            
                            stats[f"{prefixo}_ult_15"] = (total > 1.5)
                            stats[f"{prefixo}_ult_sofreu"] = sofreu
                            if g1 > 0 and g2 > 0:
                                stats[f"{prefixo}_ult_btts"] = True
                        except Exception as e:
                            print(f"        ⚠️ Erro na trava: {e}")
                    
                    # Acumuladores para os mercados
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if g1 > 0 and g2 > 0: stats[f"{prefixo}_btts"] += 1

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
            if total_mercados >= 13: break
            
            print(f"\n--- Analisando: {nome_comp} ---")
            driver.get(url)
            
            # --- O AJUSTE ESTÁ AQUI ---
            try:
                # Espera o seletor dos jogos aparecer por até 15 segundos
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".event__match"))
                )
                # Garante que o conteúdo interno (horários) também carregou
                time.sleep(3) 
            except:
                print(f"      ⚠️ Jogos não carregaram em {nome_comp}. Pulando...")
                continue
            # --------------------------

            elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")

            jogos_do_campeonato = []
            
            for el in elementos:
                if total_mercados >= 13: break
                
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
                        
                        # Captura as estatísticas do H2H
                        s = pegar_estatisticas_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall", t1, t2)
                        
                        # 1. Busca os retornos de todos os módulos
                        res_gols = gols.verificar_gols(s)  # Retorna lista [+1.5, +2.5]
                        res_btts = ambos_marcam.verificar_btts(s) # Retorna string (ex: "85%")
                        res_cd = chance_dupla.verificar_chance_dupla(s) # Retorna lista [1X, 2X]
                        
                        jogos_mercados = [] # Lista temporária para este jogo

                        # --- SEQUÊNCIA DE PRIORIDADE (MÁXIMO 3 POR JOGO) ---

                        # Prioridade 1: +1.5 Gols
                        m15 = [m for m in res_gols if "+1.5" in m]
                        if m15 and len(jogos_mercados) < 3:
                            jogos_mercados.append(f"🔶 Mercado: {m15[0]}")

                        # Prioridade 2: 1X
                        m1x = [m for m in res_cd if "1X" in m]
                        if m1x and len(jogos_mercados) < 3:
                            jogos_mercados.append(f"🔶 Mercado: {m1x[0]}")

                        # Prioridade 3: Ambas Marcam (BTTS)
                        if res_btts and len(jogos_mercados) < 3:
                            jogos_mercados.append(f"🔶 Ambas Marcam: Sim ({res_btts})")

                        # Prioridade 4: +2.5 Gols
                        m25 = [m for m in res_gols if "+2.5" in m]
                        if m25 and len(jogos_mercados) < 3:
                            jogos_mercados.append(f"🔶 Mercado: {m25[0]}")

                        # Prioridade 5: 2X
                        m2x = [m for m in res_cd if "2X" in m]
                        if m2x and len(jogos_mercados) < 3:
                            jogos_mercados.append(f"🔶 Mercado: {m2x[0]}")

                        # 2. Adiciona ao bilhete global respeitando o limite de 13
                        if jogos_mercados:
                            mercados_adicionados_neste_jogo = []
                            for mercado in jogos_mercados:
                                if total_mercados < 13:
                                    mercados_adicionados_neste_jogo.append(mercado)
                                    total_mercados += 1
                            
                            if mercados_adicionados_neste_jogo:
                                item = f"⏱️ {h_br} | {nome_comp}\n🏟️ {t1} x {t2}\n" + "\n".join(mercados_adicionados_neste_jogo)
                                jogos_do_campeonato.append(item)
                                print(f"    ✅ Adicionado: {t1} x {t2} ({len(mercados_adicionados_neste_jogo)} mercados)")

                except Exception as e:
                    print(f"    ❌ Erro ao processar jogo: {e}")
                    continue
            
            if jogos_do_campeonato:
                bilhete_agrupado.append("\n\n".join(jogos_do_campeonato))

        if bilhete_agrupado:
            cabecalho = f"🎫 *BILHETE GERADO - {hoje_ref.strftime('%d/%m')}*\n"
            cabecalho += "🎯 *MERCADOS: GOLS / BTTS / 1X-2X*\n\n"
            corpo = "\n\n----------------------------------------------\n\n".join(bilhete_agrupado)
            rodape = f"\n\n---\n📊 Total de mercados: {total_mercados}\n💎 *Apostar:* [Betano](https://br.betano.com/)"
            enviar_telegram(cabecalho + corpo + rodape)
        else:
            print("\nNenhum jogo encontrado nos critérios.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
        
