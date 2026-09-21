import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def mesmo_time(nome_busca, nome_tabela):
    """
    Verifica se o nome vindo do site (ex: 'Estud dLP') corresponde ao time buscado (ex: 'Estudiantes').
    """
    if not nome_busca or not nome_tabela:
        return False
    nb = nome_busca.lower().strip()
    nt = nome_tabela.lower().strip()
    
    # 1. Verificação de substring direta
    if nb in nt or nt in nb:
        return True
    
    # 2. Comparação pelos primeiros 3 caracteres do primeiro nome
    palavra_busca = nb.split()[0]
    palavra_tabela = nt.split()[0]
    if len(palavra_busca) >= 3 and len(palavra_tabela) >= 3:
        if palavra_busca[:3] == palavra_tabela[:3]:
            return True
            
    return False

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, nome_comp=""):
    """
    Raspa as métricas gerais (Overall, For, Against) e o histórico dos últimos 5 jogos
    de cada time no StatsHub, lidando com abreviações nos nomes.
    """
    overall_casa, for_casa, against_casa = "N/A", "N/A", "N/A"
    overall_fora, for_fora, against_fora = "N/A", "N/A", "N/A"
    
    lista_jogos_casa = []
    lista_jogos_fora = []

    try:
        driver.get(url_jogo)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # 1. Clique na aba "Team Stats"
        try:
            aba_team_stats = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Team Stats')]"))
            )
            driver.execute_script("arguments[0].click();", aba_team_stats)
            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Aviso: Falha ao clicar na aba Team Stats: {e}")

        # 2. Rola a página em etapas para renderizar os blocos e tabelas inferiores
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # 3. EXTRAÇÃO DAS MÉTRICAS (OVERALL, FOR, AGAINST)
        blocos = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-3')]")

        if len(blocos) >= 1:
            spans_casa = blocos[0].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_casa) >= 3:
                overall_casa = spans_casa[0].text.strip()
                for_casa = spans_casa[1].text.strip()
                against_casa = spans_casa[2].text.strip()

        if len(blocos) >= 2:
            spans_fora = blocos[1].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_fora) >= 3:
                overall_fora = spans_fora[0].text.strip()
                for_fora = spans_fora[1].text.strip()
                against_fora = spans_fora[2].text.strip()

        # 4. EXTRAÇÃO DAS LINHAS DE JOGOS (TR)
        linhas = driver.find_elements(By.XPATH, "//tr[.//td]")

        for linha in linhas:
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if len(colunas) >= 5:
                    data = colunas[0].text.strip()
                    home_nome = colunas[1].text.strip()
                    gols_casa = colunas[2].text.strip()
                    gols_fora = colunas[3].text.strip()
                    away_nome = colunas[4].text.strip()

                    if data and gols_casa.isdigit() and gols_fora.isdigit():
                        info_jogo = f"{data} | {home_nome} {gols_casa} - {gols_fora} {away_nome}"

                        # Filtra últimos 5 jogos do Mandante (Lanús)
                        if mesmo_time(t1, home_nome) or mesmo_time(t1, away_nome):
                            if len(lista_jogos_casa) < 5 and info_jogo not in lista_jogos_casa:
                                lista_jogos_casa.append(info_jogo)

                        # Filtra últimos 5 jogos do Visitante (Estudiantes / Estud dLP)
                        if mesmo_time(t2, home_nome) or mesmo_time(t2, away_nome):
                            if len(lista_jogos_fora) < 5 and info_jogo not in lista_jogos_fora:
                                lista_jogos_fora.append(info_jogo)
            except Exception:
                continue

    except Exception as e:
        print(f"   ⚠️ Erro durante a raspagem: {e}")

    # LOG ORGANIZADO NO TERMINAL
    print("\n" + "="*60)
    print("📊 STATSHUB - MÉTRICAS & HISTÓRICO DE JOGOS")
    print("="*60)
    print(f"🏠 {t1} (Casa):")
    print(f"   • Overall : {overall_casa} | For: {for_casa} | Against: {against_casa}")
    print("   • Últimos 5 jogos:")
    for j in lista_jogos_casa:
        print(f"     - {j}")

    print("-" * 60)
    print(f"✈️ {t2} (Fora):")
    print(f"   • Overall : {overall_fora} | For: {for_fora} | Against: {against_fora}")
    print("   • Últimos 5 jogos:")
    for j in lista_jogos_fora:
        print(f"     - {j}")
    print("="*60 + "\n")

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
