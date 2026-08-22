import time
import re
import links 
from ligas import liga_permite_classificacao 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def formatar_rota_h2h(url_base, sub_rota=""):
    """
    Limpa qualquer parâmetro de busca (como ?mid=...), barras duplicadas 
    e sufixos antigos, deixando a URL limpa com /h2h/casa/ ou /h2h/fora/.
    """
    path = url_base.split('?')[0].split('#')[0].rstrip('/')

    for sufixo in ['/overall', '/casa', '/fora']:
        if path.endswith(sufixo):
            path = path[:-len(sufixo)]

    if not path.endswith('/h2h'):
        path = f"{path}/h2h"

    if sub_rota:
        path = f"{path}/{sub_rota}"

    return f"{path}/"

def obter_url_real_h2h(driver, url_jogo_input):
    """
    Resolve IDs curtos (ex: .../jogo/Ak19JDbf/) abrindo a página raiz do jogo
    e pegando a URL completa com os slugs dos dois times gerada pelo Flashscore.
    """
    if '/futebol/' in url_jogo_input:
        return url_jogo_input.split('?')[0]

    match_id = re.search(r'/jogo/([A-Za-z0-9]+)', url_jogo_input)
    id_jogo = match_id.group(1) if match_id else url_jogo_input.strip('/')
    
    url_raiz = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
    driver.get(url_raiz)
    time.sleep(1.5)
    
    return driver.current_url.split('?')[0]

def pegar_estatisticas_h2h(driver, url_jogo_base, t1, t2, nome_comp=""):
    stats = {
        "link_betano": None,
        "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_btts": 0, 
        "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_btts": 0, 
        
        # Chaves de Padrão e Posição
        "mandante_posicao": None,
        "visitante_posicao": None,
        "mandante_vitorias_casa": 0,
        "visitante_vitorias_fora": 0,
        "mandante_sem_derrota_casa": 0,
        "visitante_sem_derrota_fora": 0,
        "visitante_derrotas_fora": 0,
        "visitante_gols_sofridos_fora": 0.0,
        "mandante_gols_sofridos_casa": 0.0,
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
        url_real = obter_url_real_h2h(driver, url_jogo_base)

        # Captura do link Betano
        try:
            print(f"      🔗 Capturando link Betano para {t1} x {t2}...")
            url_capturada = links.extrair_url_betano(driver)
            if url_capturada:
                stats["link_betano"] = url_capturada
            else:
                t1_q, t2_q = t1.replace(" ", "%20"), t2.replace(" ", "%20")
                stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"
        except Exception as e_link:
            print(f"      ⚠️ Erro ao capturar link Betano: {e_link}")
            t1_q, t2_q = t1.replace(" ", "%20"), t2.replace(" ", "%20")
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

                            if tipo == "casa":
                                if i == 0: stats["t1_placar_1"] = placar_str
                                if total > 1.5: stats["casa_15"] += 1
                                if total > 2.5: stats["casa_25"] += 1
                                if total <= 3: stats["casa_35_under"] += 1
                                if total <= 4: stats["casa_45_under"] += 1 
                                if g1 > 0 and g2 > 0: stats["casa_btts"] += 1
                                
                                stats["mandante_gols_feitos_casa"] += float(g1)
                                stats["mandante_gols_sofridos_casa"] += float(g2)
                                if g1 > 0: stats["mandante_jogos_com_gol_casa"] += 1
                                
                                if g1 > g2:
                                    res_atual = "V"
                                    stats["mandante_vitorias_casa"] += 1
                                    stats["mandante_sem_derrota_casa"] += 1
                                elif g1 < g2:
                                    res_atual = "D"
                                else:
                                    res_atual = "E"
                                    stats["mandante_sem_derrota_casa"] += 1
                                
                                if i == 0: stats["t1_resultado_1"] = res_atual

                            elif tipo == "fora":
                                if i == 0: stats["t2_placar_1"] = placar_str
                                if total > 1.5: stats["fora_15"] += 1
                                if total > 2.5: stats["fora_25"] += 1
                                if total <= 3: stats["fora_35_under"] += 1  # 🟢 Corrigido para salvar no visitante
                                if total <= 4: stats["fora_45_under"] += 1  # 🟢 Corrigido para salvar no visitante
                                if g1 > 0 and g2 > 0: stats["fora_btts"] += 1
                                
                                stats["visitante_gols_feitos_fora"] += float(g2)
                                stats["visitante_gols_sofridos_fora"] += float(g1)
                                if g2 > 0: stats["visitante_jogos_com_gol_fora"] += 1
                                
                                if g2 > g1:
                                    res_atual = "V"
                                    stats["visitante_vitorias_fora"] += 1
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

        # 🟢 TRAVA UTILIZANDO A FUNÇÃO IMPORTADA DO LIGAS.PY
        if liga_permite_classificacao(nome_comp):
            print(f"      📊 Liga permitida para tabela ({nome_comp}). Buscando posições...")
            posicoes = pegar_posicao_tabela(driver, url_jogo_base, t1, t2)
            stats.update(posicoes)
        else:
            print(f"      ℹ️ Liga fora de pontos corridos ({nome_comp}). Ignorando tabela.")

    except Exception as e_geral:
        print(f"      ⚠️ Erro ao resolver URL do jogo: {e_geral}")

    return stats

def pegar_posicao_tabela(driver, url_jogo_base, t1, t2):
    """
    Acessa a aba de classificação usando o ?mid= extraído da URL real
    e busca a posição exata do mandante e do visitante na tabela.
    """
    posicoes = {"mandante_posicao": None, "visitante_posicao": None}
    try:
        url_real = obter_url_real_h2h(driver, url_jogo_base)
        url_classificacao = f"{url_real}/classificacao/classificacoes/geral/"
        
        # 🟢 Navega para a aba de classificação
        driver.get(url_classificacao)
        
        # 🟢 Trava de segurança: aguarda a tabela carregar na tela antes de buscar os elementos
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".table__row, [class*='table__row']"))
        )
        
        linhas_tabela = driver.find_elements(By.CSS_SELECTOR, ".table__row, [class*='table__row']")
        
        for linha in linhas_tabela:
            try:
                div_rank = linha.find_element(By.CSS_SELECTOR, ".tableCellRank")
                a_team = linha.find_element(By.CSS_SELECTOR, ".tableCellParticipant__name")
                
                if div_rank and a_team:
                    pos_str = div_rank.text.strip().replace('.', '')
                    nome_time = a_team.text.strip().lower()
                    pos_int = int(pos_str)
                    
                    if t1.lower() in nome_time or nome_time in t1.lower():
                        posicoes["mandante_posicao"] = pos_int
                    elif t2.lower() in nome_time or nome_time in t2.lower():
                        posicoes["visitante_posicao"] = pos_int
            except Exception:
                continue
                
    except Exception as e:
        print(f"      ⚠️ Erro ao raspar posições da tabela: {e}")
        
    return posicoes
    
