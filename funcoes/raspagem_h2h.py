import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def obter_url_real_h2h(driver, url_jogo_input):
    """
    Resolve IDs curtos (ex: .../jogo/Ak19JDbf/) abrindo a página raiz do jogo
    e pegando a URL completa com os slugs dos dois times gerada pelo Flashscore.
    """
    # Se a URL já contiver o padrão longo com os nomes dos times, só limpa o final
    if '/futebol/' in url_jogo_input:
        url_base = url_jogo_input.split('#')[0].rstrip('/')
        for sufixo in ['/overall', '/casa', '/fora']:
            if url_base.endswith(sufixo):
                url_base = url_base[:-len(sufixo)]
        if not url_base.endswith('/h2h'):
            url_base = f"{url_base}/h2h"
        return url_base

    # Caso seja a URL com ID curto (ex: .../jogo/Ak19JDbf/ ou só Ak19JDbf)
    match_id = re.search(r'/jogo/([A-Za-z0-9]+)', url_jogo_input)
    id_jogo = match_id.group(1) if match_id else url_jogo_input.strip('/')
    
    url_raiz = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
    driver.get(url_raiz)
    time.sleep(1.5)  # Aguarda o redirecionamento do Flashscore para a URL longa
    
    # Captura a URL expandida pelo navegador (ex: .../jogo/futebol/remo-2i0B6Zul/santos-n3QdnjFB/)
    url_redirecionada = driver.current_url.split('#')[0].rstrip('/')
    
    if not url_redirecionada.endswith('/h2h'):
        url_redirecionada = f"{url_redirecionada}/h2h"
        
    return url_redirecionada

def pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2):
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_btts": 0, 
        "casa_vitorias_recente": 0, "ultimo_gols_casa": 0, "t1_resultado_1": "",
        "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_btts": 0, 
        "fora_vitorias_recente": 0, "ultimo_gols_fora": 0, "t2_resultado_1": "",
        "h2h_jogos": 0, "h2h_vitorias_t1": 0, "h2h_vitorias_t2": 0, "h2h_empates": 0,
        "h2h_res_1": "", "h2h_res_2": "", 
        "h2h_geral_res_1": "", "h2h_geral_res_2": "", "h2h_geral_res_3": "", "h2h_geral_res_4": "", "h2h_geral_res_5": "",
        "t1_placar_1": None, "t2_placar_1": None,     
        "h2h_placar_1": None, "h2h_placar_2": None,   
        "pular_gols": False,
        "url_h2h_base": url_jogo_base,
        "historico_chutes": {}, 
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {}
    }

    try:
        # Resolvendo a URL completa antes de navegar nas sub-rotas
        url_h2h_completa = obter_url_real_h2h(driver, url_jogo_base)
        
        rotas = [
            ("casa", f"{url_h2h_completa}/casa/"),
            ("fora", f"{url_h2h_completa}/fora/")
        ]

        for tipo, url in rotas:
            try:
                driver.get(url)
                
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']"))
                )
                
                secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
                if secoes:
                    linhas = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")[:5]
                    
                    for i, linha in enumerate(linhas):
                        try:
                            res_el = linha.find_element(By.CSS_SELECTOR, ".h2h__result, [class*='h2h__result']")
                            nums = re.findall(r'\d+', res_el.text)
                            if len(nums) < 2: 
                                continue
                            
                            g1, g2 = int(nums[0]), int(nums[1])
                            placar_str = f"{g1}-{g2}"
                            total = g1 + g2

                            # 🎯 ABA MANDANTE - CASA (Time Mandante = g1)
                            if tipo == "casa":
                                if i == 0: 
                                    stats["t1_placar_1"] = placar_str
                                    stats["ultimo_gols_casa"] = total
                                
                                if total > 1.5: stats["casa_15"] += 1
                                if total > 2.5: stats["casa_25"] += 1
                                if total <= 3: stats["casa_35_under"] += 1
                                if total <= 4: stats["casa_45_under"] += 1 
                                if g1 > 0 and g2 > 0: stats["casa_btts"] += 1
                                
                                if g1 > g2:
                                    res_atual = "V"
                                    stats["casa_vitorias_recente"] += 1
                                elif g1 < g2:
                                    res_atual = "D"
                                else:
                                    res_atual = "E"
                                
                                if i == 0: stats["t1_resultado_1"] = res_atual

                            # 🎯 ABA VISITANTE - FORA (Time Visitante = g2)
                            elif tipo == "fora":
                                if i == 0: 
                                    stats["t2_placar_1"] = placar_str
                                    stats["ultimo_gols_fora"] = total
                                
                                if total > 1.5: stats["fora_15"] += 1
                                if total > 2.5: stats["fora_25"] += 1
                                if total <= 3: stats["fora_35_under"] += 1
                                if total <= 4: stats["fora_45_under"] += 1 
                                if g1 > 0 and g2 > 0: stats["fora_btts"] += 1
                                
                                if g2 > g1:
                                    res_atual = "V"
                                    stats["fora_vitorias_recente"] += 1
                                elif g2 < g1:
                                    res_atual = "D"
                                else:
                                    res_atual = "E"
                                
                                if i == 0: stats["t2_resultado_1"] = res_atual

                        except Exception:
                            continue

            except Exception as e:
                print(f"      ⚠️ Erro ao raspar jogos do {tipo.upper()} ({url}): {e}")

    except Exception as e_geral:
        print(f"      ⚠️ Erro ao resolver URL do jogo: {e_geral}")

    return stats
        
