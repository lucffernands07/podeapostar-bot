import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Importações dos seus módulos
from testes.teste_ligas import TESTE_COMPETICOES
from mercados import gols, ambos_marcam, chance_dupla, vitoria_casa, jogadores, cartoes
import odds
import bingo357

# Importações das funções de raspagem
from funcoes.raspagem_h2h import pegar_estatisticas_h2h
from funcoes.raspagem_scouts import pegar_scouts_avancados

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = configurar_driver()
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    lista_para_filtros = []      
    total_mercados = 0 

    try:
        for nome_comp, url in TESTE_COMPETICOES.items():
            if total_mercados >= 200: break
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
                        
                        # Raspagem
                        s_inicial = pegar_estatisticas_h2h(driver, url_h2h_final, t1, t2)
                        s = pegar_scouts_avancados(driver, s_inicial, t1, t2)
                        
                        # Processamento de Mercados
                        mercados_para_processar = []
                        # ... (adicionar suas chamadas dos módulos gols, ambos_marcam, etc aqui) ...

                        # Validação de Odds e adição na lista_para_filtros
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                valor_odd_str = v_odds.get(item["chave"], "1.50")
                                if float(valor_odd_str.replace(',', '.')) >= 1.25:
                                    lista_para_filtros.append({"time_casa": t1, "time_fora": t2, "mercado": item["texto"], "odd": valor_odd_str, "liga": nome_comp})
                                    total_mercados += 1
                except Exception:
                    continue

        # --- PROCESSAMENTO FINAL (Fora do loop) ---
        if lista_para_filtros:
            print(f"\n🧪 TESTE: {len(lista_para_filtros)} mercados coletados.")
            bilhete_elite = bingo357.montar_bilhete_elite_main(lista_para_filtros)
            print(f"🧪 Teste Bingo Elite: {len(bilhete_elite) if bilhete_elite else 0} bilhetes.")
            novos_bingos = bingo357.montar_bilhetes_estrategicos(lista_para_filtros)
            print(f"🧪 Teste Bingos Estratégicos: {len(novos_bingos) if novos_bingos else 0} conjuntos.")
        else:
            print("\n⚠️ Nenhum mercado passou nos filtros.")

    except Exception as e:
        print(f"❌ Erro Crítico no Teste: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
