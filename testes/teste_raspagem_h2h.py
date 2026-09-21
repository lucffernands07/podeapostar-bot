import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, nome_comp=""):
    """
    Raspa os últimos 5 jogos do mandante (casa) e visitante (fora) no StatsHub
    e retorna o dicionário 'stats' pronto para os módulos de regras.
    """
    stats = {
        "link_betano": None,
        "casa_05": 0, "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, "casa_55_under": 0, "casa_btts": 0, 
        "fora_05": 0, "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, "fora_55_under": 0, "fora_btts": 0, 
        
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

        "t1_placar_1": None, "t2_placar_1": None,     
        "t1_resultado_1": None, "t2_resultado_1": None,
        "pular_gols": False,
        "url_h2h_base": url_jogo,
        "historico_chutes": {}, 
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {}
    }

    # Gera link de busca na Betano
    t1_q, t2_q = t1.replace(" ", "%20"), t2.replace(" ", "%20")
    stats["link_betano"] = f"https://www.betano.bet.br/busca/?q={t1_q}%20x%20{t2_q}"

    try:
        driver.get(url_jogo)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        # 1. Clicar na aba 'Team Stats' se existir
        try:
            btn_team_stats = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Team Stats')] | //div[contains(text(), 'Team Stats')]"))
            )
            btn_team_stats.click()
            time.sleep(2)
        except Exception:
            pass # Se já estiver na aba correta ou for carregamento direto

        # 2. Alternar e analisar "casa" (Mandante) e "fora" (Visitante)
        perspectivas = ["casa", "fora"]

        for tipo in perspectivas:
            try:
                # Tenta alternar o menu suspenso de filtro para Home/Away
                try:
                    filtro = driver.find_element(By.XPATH, "//button[contains(., 'Fixtures') or contains(., 'Home') or contains(., 'Away') or contains(., 'All')]")
                    filtro.click()
                    time.sleep(1)

                    alvo_filtro = "Home" if tipo == "casa" else "Away"
                    opcao = driver.find_element(By.XPATH, f"//li[contains(., '{alvo_filtro}')] | //button[contains(., '{alvo_filtro}')] | //div[contains(text(), '{alvo_filtro}')]")
                    opcao.click()
                    time.sleep(2)
                except Exception:
                    pass

                # Localiza as linhas da tabela contendo os jogos
                linhas = driver.find_elements(By.XPATH, "//tbody/tr | //div[contains(@class, 'match')] | //div[contains(@class, 'row')]")
                linhas_validas = []

                # Filtra apenas linhas que possuem um placar numérico (ex: "2 - 1" ou "1-0")
                for l in linhas:
                    texto = l.text
                    if re.search(r'\d+\s*[\-–:]\s*\d+', texto):
                        linhas_validas.append(l)
                    if len(linhas_validas) == 5:
                        break

                print(f"   🔍 [{tipo.upper()}] Encontrados {len(linhas_validas)} jogos no histórico.")

                for i, linha in enumerate(linhas_validas):
                    try:
                        match_placar = re.search(r'(\d+)\s*[\-–:]\s*(\d+)', linha.text)
                        if not match_placar:
                            continue

                        g1, g2 = int(match_placar.group(1)), int(match_placar.group(2))
                        placar_str = f"{g1}-{g2}"
                        total = g1 + g2

                        if tipo == "casa":
                            if i == 0: 
                                stats["t1_placar_1"] = placar_str
                            
                            if total > 0.5: stats["casa_05"] += 1
                            if total > 1.5: stats["casa_15"] += 1
                            if total > 2.5: stats["casa_25"] += 1
                            if total <= 3: stats["casa_35_under"] += 1
                            if total <= 4: stats["casa_45_under"] += 1
                            if total <= 5: stats["casa_55_under"] += 1
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
                            if i == 0: 
                                stats["t2_placar_1"] = placar_str
                            
                            if total > 0.5: stats["fora_05"] += 1
                            if total > 1.5: stats["fora_15"] += 1
                            if total > 2.5: stats["fora_25"] += 1
                            if total <= 3: stats["fora_35_under"] += 1
                            if total <= 4: stats["fora_45_under"] += 1
                            if total <= 5: stats["fora_55_under"] += 1
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

                    except Exception as e_linha:
                        continue

            except Exception as e_tipo:
                print(f"      ⚠️ Erro ao processar histórico {tipo.upper()}: {e_tipo}")

    except Exception as e_geral:
        print(f"      ⚠️ Erro geral ao raspar StatsHub: {e_geral}")

    return stats
