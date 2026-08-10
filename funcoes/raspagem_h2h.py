import time
import re
import links  # 🟢 Import do links.py restaurado
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def formatar_rota_h2h(url_base, sub_rota=""):
    """
    Limpa qualquer parâmetro de busca (como ?mid=...), barras duplicadas 
    e sufixos antigos, deixando a URL limpa com /h2h/casa/ ou /h2h/fora/.
    """
    # 1. Remove qualquer parâmetro após o '?' (?mid=..., etc.) e o '#'
    path = url_base.split('?')[0].split('#')[0].rstrip('/')

    # 2. Limpa sufixos antigos de abas caso existam
    for sufixo in ['/overall', '/casa', '/fora']:
        if path.endswith(sufixo):
            path = path[:-len(sufixo)]

    # 3. Garante que a rota /h2h está no final da base
    if not path.endswith('/h2h'):
        path = f"{path}/h2h"

    # 4. Adiciona a sub-rota (/casa ou /fora)
    if sub_rota:
        path = f"{path}/{sub_rota}"

    return f"{path}/"

def obter_url_real_h2h(driver, url_jogo_input):
    """
    Resolve IDs curtos (ex: .../jogo/Ak19JDbf/) abrindo a página raiz do jogo
    e pegando a URL completa com os slugs dos dois times gerada pelo Flashscore.
    """
    # Se a URL já contiver o padrão longo com os nomes dos times
    if '/futebol/' in url_jogo_input:
        return url_jogo_input.split('?')[0]

    # Caso seja a URL com ID curto (ex: .../jogo/Ak19JDbf/ ou só Ak19JDbf)
    match_id = re.search(r'/jogo/([A-Za-z0-9]+)', url_jogo_input)
    id_jogo = match_id.group(1) if match_id else url_jogo_input.strip('/')
    
    url_raiz = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
    driver.get(url_raiz)
    time.sleep(1.5)  # Aguarda o redirecionamento do Flashscore para a URL longa
    
    # Captura a URL expandida pelo navegador sem parâmetros de query (?mid=...)
    return driver.current_url.split('?')[0]

def pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2):
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_btts": 0, 
        "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_btts": 0, 
        
        # 🟢 CHAVES PADRÃO UNIFICADAS (Chance Dupla e Vitórias)
        "mandante_vitorias_casa": 0,
        "visitante_vitorias_fora": 0,
        "mandante_sem_derrota_casa": 0,
        "visitante_sem_derrota_fora": 0,
        "visitante_derrotas_fora": 0,
        "visitante_gols_sofridos_fora": 0.0,
        "mandante_gols_sofridos_casa": 0.0,

        # 🟢 CHAVES DE GOLS EXIGIDAS PELO GOLS.PY ADICIONADAS
        "mandante_gols_feitos_casa": 0.0,
        "visitante_gols_feitos_fora": 0.0,
        "mandante_jogos_com_gol_casa": 0,
        "visitante_jogos_com_gol_fora": 0,

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
        url_real = obter_url_real_h2h(driver, url_jogo_base)

        # -----------------------------------------------------------------
        # 🟢 CAPTURA RESTAURADA DO LINK DA BETANO (COM FALLBACK SEGURO)
        # -----------------------------------------------------------------
        try:
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            url_capturada = links.extrair_url_betano(driver)
            
            if url_capturada:
                stats["link_betano"] = url_capturada
            else:
                t1_q = t1.replace(" ", "%20")
                t2_q = t2.replace(" ", "%20")
                stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano: {e_link}")
            t1_q = t1.replace(" ", "%20")
            t2_q = t2.replace(" ", "%20")
            stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"
        
        rotas = [
            ("casa", formatar_rota_h2h(url_real, "casa")),
            ("fora", formatar_rota_h2h(url_real, "fora"))
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
                                
                                if total > 1.5: stats["casa_15"] += 1
                                if total > 2.5: stats["casa_25"] += 1
                                if total <= 3: stats["casa_35_under"] += 1
                                if total <= 4: stats["casa_45_under"] += 1 
                                if g1 > 0 and g2 > 0: stats["casa_btts"] += 1
                                
                                # Contabiliza gols feitos e sofridos do mandante em casa
                                stats["mandante_gols_feitos_casa"] += float(g1)
                                stats["mandante_gols_sofridos_casa"] += float(g2)
                                if g1 > 0:
                                    stats["mandante_jogos_com_gol_casa"] += 1
                                
                                if g1 > g2:
                                    res_atual = "V"
                                    stats["mandante_vitorias_casa"] += 1  # Chave padrão unificada
                                    stats["mandante_sem_derrota_casa"] += 1
                                elif g1 < g2:
                                    res_atual = "D"
                                else:
                                    res_atual = "E"
                                    stats["mandante_sem_derrota_casa"] += 1 # Empate conta como sem derrota
                                
                                if i == 0: stats["t1_resultado_1"] = res_atual

                            # 🎯 ABA VISITANTE - FORA (Time Visitante = g2)
                            elif tipo == "fora":
                                if i == 0: 
                                    stats["t2_placar_1"] = placar_str
                                
                                if total > 1.5: stats["fora_15"] += 1
                                if total > 2.5: stats["fora_25"] += 1
                                if total <= 3: stats["fora_35_under"] += 1
                                if total <= 4: stats["fora_45_under"] += 1 
                                if g1 > 0 and g2 > 0: stats["fora_btts"] += 1
                                
                                # Contabiliza gols feitos e sofridos do visitante fora
                                stats["visitante_gols_feitos_fora"] += float(g2)
                                stats["visitante_gols_sofridos_fora"] += float(g1)
                                if g2 > 0:
                                    stats["visitante_jogos_com_gol_fora"] += 1
                                
                                if g2 > g1:
                                    res_atual = "V"
                                    stats["visitante_vitorias_fora"] += 1  # Chave padrão unificada
                                    stats["visitante_sem_derrota_fora"] += 1
                                elif g2 < g1:
                                    res_atual = "D"
                                    stats["visitante_derrotas_fora"] += 1
                                else:
                                    res_atual = "E"
                                    stats["visitante_sem_derrota_fora"] += 1
                                
                                if i == 0: stats["t2_resultado_1"] = res_atual

                        except Exception:
                            continue

            except Exception as e:
                print(f"      ⚠️ Erro ao raspar jogos do {tipo.upper()} ({url}): {e}")

    except Exception as e_geral:
        print(f"      ⚠️ Erro ao resolver URL do jogo: {e_geral}")

    return stats
        
