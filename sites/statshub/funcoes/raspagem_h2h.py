import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def mesmo_time(nome_busca, nome_tabela):
    """
    Verifica de forma flexível se o nome vindo do site
    corresponde ao time buscado.
    """
    if not nome_busca or not nome_tabela:
        return False
    nb = nome_busca.lower().strip()
    nt = nome_tabela.lower().strip()
    
    if nb in nt or nt in nb:
        return True
    
    palavras_busca = [p for p in nb.split() if len(p) >= 3]
    palavras_tabela = [p for p in nt.split() if len(p) >= 3]
    
    for pb in palavras_busca:
        for pt in palavras_tabela:
            if pb[:3] == pt[:3] and (pb in pt or pt in pb or pb[:4] == pt[:4]):
                return True
                
    return False

def eh_amistoso(nome_competicao, url_competicao=""):
    """
    Retorna True se a competição for um amistoso.
    """
    termos_proibidos = ["friendly", "amistoso", "int. friendly", "friendly games"]
    
    comp_lower = nome_competicao.lower()
    url_lower = url_competicao.lower()
    
    for termo in termos_proibidos:
        if termo in comp_lower or termo in url_lower:
            return True
            
    return False

def aguardar_elemento_ou_texto(driver, xpath, timeout=12):
    """
    Aguarda até que elementos pelo XPath existam e tenham texto visível/carregado.
    """
    fim = time.time() + timeout
    while time.time() < fim:
        try:
            elementos = driver.find_elements(By.XPATH, xpath)
            for el in elementos:
                if el.text.strip() and "N/A" not in el.text.strip():
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, horario="", aba_principal=None):
    """
    Raspa as métricas gerais e o histórico detalhado com o nome da competição
    para cada jogo do histórico (excluindo amistosos).
    """
    overall_casa, for_casa, against_casa = "N/A", "N/A", "N/A"
    overall_fora, for_fora, against_fora = "N/A", "N/A", "N/A"
    
    lista_jogos_casa = []
    lista_jogos_fora = []

    texto_horario = f" - {horario}" if horario else ""
    print(f"🏟️ Jogo: {t1} x {t2}{texto_horario}")
    print(f"🔗 URL: {url_jogo}\n")

    if aba_principal is None:
        aba_principal = driver.current_window_handle

    try:
        driver.execute_script("window.open(arguments[0], '_blank');", url_jogo)
        
        novas_abas = [handle for handle in driver.window_handles if handle != aba_principal]
        if novas_abas:
            driver.switch_to.window(novas_abas[-1])

        # 1. Espera inicial do carregamento do body
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # 2. Rolagem gradativa para carregar componentes dinâmicos (Lazy Loading)
        driver.execute_script("window.scrollTo(0, 400);")
        time.sleep(1)

        # 3. AGUARDA AS MÉTRICAS APARECEREM NO DOM
        xpath_spans = "//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]"
        aguardar_elemento_ou_texto(driver, xpath_spans, timeout=10)

        # Extração das métricas (Overall, For, Against)
        blocos = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-3')]")

        if len(blocos) >= 1:
            spans_casa = blocos[0].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_casa) >= 3:
                overall_casa = spans_casa[0].text.strip() or "N/A"
                for_casa = spans_casa[1].text.strip() or "N/A"
                against_casa = spans_casa[2].text.strip() or "N/A"

        if len(blocos) >= 2:
            spans_fora = blocos[1].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_fora) >= 3:
                overall_fora = spans_fora[0].text.strip() or "N/A"
                for_fora = spans_fora[1].text.strip() or "N/A"
                against_fora = spans_fora[2].text.strip() or "N/A"

        # 4. EXTRAÇÃO DOS JOGOS E COMPETIÇÃO (COM RETRY)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)

        def ler_tabela():
            linhas = driver.find_elements(By.XPATH, "//tr[.//td]")
            for linha in linhas:
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    if len(colunas) >= 6:
                        data = colunas[0].text.strip()
                        home_nome = colunas[1].text.strip()
                        gols_casa = colunas[2].text.strip()
                        gols_fora = colunas[3].text.strip()
                        away_nome = colunas[4].text.strip()
                        
                        coluna_comp = colunas[5]
                        nome_comp = coluna_comp.text.strip()
                        href_comp = ""
                        
                        try:
                            link_elem = coluna_comp.find_element(By.TAG_NAME, "a")
                            href_comp = link_elem.get_attribute("href") or ""
                            if not nome_comp:
                                nome_comp = link_elem.text.strip()
                        except Exception:
                            pass

                        if eh_amistoso(nome_comp, href_comp):
                            continue

                        if data and gols_casa.isdigit() and gols_fora.isdigit():
                            dados_jogo = {
                                "data": data,
                                "home": home_nome,
                                "gols_casa": int(gols_casa),
                                "gols_fora": int(gols_fora),
                                "away": away_nome,
                                "competicao": nome_comp
                            }

                            if mesmo_time(t1, home_nome) or mesmo_time(t1, away_nome):
                                if len(lista_jogos_casa) < 5 and dados_jogo not in lista_jogos_casa:
                                    lista_jogos_casa.append(dados_jogo)

                            if mesmo_time(t2, home_nome) or mesmo_time(t2, away_nome):
                                if len(lista_jogos_fora) < 5 and dados_jogo not in lista_jogos_fora:
                                    lista_jogos_fora.append(dados_jogo)
                except Exception:
                    continue

        # Tenta ler a tabela até 3 vezes caso demore a carregar
        for tentativa in range(3):
            ler_tabela()
            if lista_jogos_casa or lista_jogos_fora:
                break
            driver.execute_script(f"window.scrollTo(0, {800 + (tentativa * 400)});")
            time.sleep(2)

    except Exception as e:
        print(f"    ⚠️ Erro durante a raspagem de {t1} x {t2}: {e}")

    finally:
        try:
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(aba_principal)
        except Exception:
            pass

    # LOG PRINT
    print("============================================================")
    print("📊 STATSHUB - MÉTRICAS & HISTÓRICO COM COMPETIÇÕES")
    print("============================================================")
    print(f"🏠 {t1} (Casa):")
    print(f"    • Overall : {overall_casa} | For: {for_casa} | Against: {against_casa}")
    print("    • Últimos 5 jogos oficiais:")
    for j in lista_jogos_casa:
        print(f"      - {j['data']} | {j['home']} {j['gols_casa']} x {j['gols_fora']} {j['away']} | 🏆 {j['competicao']}")

    print("-" * 60)
    print(f"✈️ {t2} (Fora):")
    print(f"    • Overall : {overall_fora} | For: {for_fora} | Against: {against_fora}")
    print("    • Últimos 5 jogos oficiais:")
    for j in lista_jogos_fora:
        print(f"      - {j['data']} | {j['home']} {j['gols_casa']} x {j['gols_fora']} {j['away']} | 🏆 {j['competicao']}")
    print("============================================================\n")

    return {
        "overall_casa": overall_casa,
        "for_casa": for_casa,
        "against_casa": against_casa,
        "overall_fora": overall_fora,
        "for_fora": for_fora,
        "against_fora": against_fora,
        "lista_jogos_casa": lista_jogos_casa,
        "lista_jogos_fora": lista_jogos_fora,
        "pular_gols": False
        }
                    
