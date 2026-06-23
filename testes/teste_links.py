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
        for nome_comp, url in TESTE_COMPETICOES.items():
            if total_mercados >= 200: break 
            print(f"\n--- Analisando: {nome_comp} ---")
            
            try:
                driver.get(url)
                time.sleep(4)
                elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
            except Exception as e:
                if "session" in str(e).lower():
                    driver = configurar_driver()
                    driver.get(url)
                    time.sleep(4)
                    elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
                else: continue
            
            for el in elementos:
                try:
                    tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                    tempo_raw = tempo_el.text.strip()
                    if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]): continue

                    partes_tempo = tempo_raw.split()
                    if not partes_tempo or ":" not in partes_tempo[-1]: continue
                    
                    h_obj = datetime.strptime(partes_tempo[-1], "%H:%M")
                    aceitar = False
                    if amanha_no_site in tempo_raw:
                        if h_obj.hour <= 3: aceitar = True
                    elif "." not in tempo_raw:
                        if (h_obj - timedelta(hours=3)).hour >= 7: aceitar = True

                    if aceitar:
                        times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                        t1, t2 = times[0].text.strip(), times[1].text.strip()
                        id_jogo = el.get_attribute('id').split('_')[-1]
                        
                        # Raspagem
                        s = pegar_scouts_avancados(driver, pegar_estatisticas_h2h(driver, f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall", t1, t2), t1, t2)
                        
                        mercados_para_processar = []

                        # Gols
                        for rg in gols.verificar_gols(s):
                            mercados_para_processar.append({"texto": rg['mercado'], "chave": rg['tipo']})

                        # Ambos Marcam
                        res_btts = ambos_marcam.verificar_btts(s)
                        if res_btts: mercados_para_processar.append({"texto": f"Ambas Marcam: Sim ({res_btts})", "chave": "BTTS"})

                        # Chance Dupla
                        s["chance_dupla_pct"] = "100%" if s.get("casa_vitorias_recente", 0) >= 4 or s.get("fora_vitorias_recente", 0) >= 4 else ("90%" if s.get("casa_vitorias_recente", 0) == 3 or s.get("fora_vitorias_recente", 0) == 3 else "80%")
                        for rc in chance_dupla.verificar_chance_dupla(s):
                            mercados_para_processar.append({"texto": rc, "chave": "1X" if "1X" in rc else "X2"})

                        # Vitória Casa
                        for rv in vitoria_casa.verificar_vitoria_casa(s):
                            mercados_para_processar.append({"texto": rv, "chave": "VITORIA_CASA"})

                        # Jogadores
                        try:
                            for rj in jogadores.verificar_destaques_jogadores(s.get("historico_chutes", {}), 3, nome_comp):
                                mercados_para_processar.append({"texto": rj['texto'], "chave": rj['chave']})
                        except: pass

                        # Cartões
                        try:
                            res_c = cartoes.analisar_dados_cartoes(s.get("historico_mandante_am", {}), s.get("historico_mandante_vm", {}), s.get("historico_visitante_am", {}), s.get("historico_visitante_vm", {}), nome_comp, 3)
                            if res_c.get("aprovado"):
                                m = res_c.get('media_confronto', 0)
                                txt = f"Cartões Totais: {'+4.5' if m >= 4.0 else '+2.5' if m >= 3.0 else '+1.5'}"
                                mercados_para_processar.append({"texto": txt, "chave": "CARTOES_CONFRONTO"})
                        except: pass

                        # Validação Odds
                        if mercados_para_processar:
                            v_odds = odds.capturar_todas_as_odds(driver, id_jogo)
                            for item in mercados_para_processar:
                                valor = float(v_odds.get(item["chave"], "1.50").replace(',', '.'))
                                if valor >= 1.25:
                                    lista_para_filtros.append({"time_casa": t1, "time_fora": t2, "mercado": item["texto"], "odd": str(valor), "liga": nome_comp})
                                    total_mercados += 1
                except Exception: continue

        # Processamento Final
        if lista_para_filtros:
            print(f"\n🧪 TESTE: {len(lista_para_filtros)} mercados coletados.")
            print(f"🧪 Teste Bingo Elite: {len(bingo357.montar_bilhete_elite_main(lista_para_filtros) or [])} bilhetes.")
            print(f"🧪 Teste Bingos Estratégicos: {len(bingo357.montar_bilhetes_estrategicos(lista_para_filtros) or [])} conjuntos.")
        else:
            print("\n⚠️ Nenhum mercado passou nos filtros.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
