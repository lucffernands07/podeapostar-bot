import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Importações dos seus módulos (Bingo removido)
from testes.teste_ligas import TESTE_COMPETICOES as COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes
import odds

# Importações das funções de raspagem
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
from funcoes.raspagem_scouts import pegar_scouts_avancados

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []      
    total_mercados = 0 

    try:
        for nome_comp, url in COMPETICOES.items():
            if total_mercados >= 200: 
                break 
            print(f"\n--- Analisando: {nome_comp} ---")
            
            try:
                driver.get(url)
                time.sleep(4)
                elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            except Exception as e:
                print(f"⚠️ Erro ao carregar liga {nome_comp}: {e}")
                continue
            
            for el in elementos:
                try:
                    tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                    tempo_raw = tempo_el.text.strip()
                    
                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                        continue

                    partes_tempo = tempo_raw.split()
                    if not partes_tempo: continue
                        
                    horario_str = partes_tempo[-1]
                    if ":" not in horario_str: continue

                    h_obj = datetime.strptime(horario_str, "%H:%M")
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
                        
                        s_inicial = pegar_estatisticas_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall", t1, t2)
                        s = pegar_scouts_avancados(driver, s_inicial, t1, t2)
                        
                        mercados_para_processar = []
                        res_gols = gols.verificar_gols(s)
                        for rg in res_gols: mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                m_chave = item["chave"]
                                valor_odd_str = "1.50" if m_chave in ["CHUTES_ALVO", "FALTAS_SOFRIDAS", "CARTOES_CONFRONTO"] else v_odds.get(m_chave, "N/A")
                                
                                try:
                                    odd_float = float(valor_odd_str.replace(',', '.'))
                                    if odd_float >= 1.25:
                                        lista_para_filtros.append({
                                            "time_casa": t1, "time_fora": t2, 
                                            "mercado": item["texto"], "odd": valor_odd_str, 
                                            "liga": nome_comp, "horario": h_br
                                        })
                                        total_mercados += 1
                                except ValueError: continue
                except: continue

    except Exception as e:
        print(f"❌ Erro Crítico no Loop: {e}")
    finally:
        driver.quit()

    # --- LISTAGEM FINAL NO TERMINAL ---
    if lista_para_filtros:
        print(f"\n🧪 TESTE FINALIZADO: {len(lista_para_filtros)} mercados encontrados.")
        for m in lista_para_filtros:
            print(f"[{m['liga']}] {m['time_casa']} x {m['time_fora']} | {m['mercado']} (@{m['odd']}) | {m['horario']}")
    else:
        print("\n⚠️ Nenhum mercado passou nos filtros.")

if __name__ == "__main__":
    main()
