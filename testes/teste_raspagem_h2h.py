import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, nome_comp=""):
    """
    Raspa as métricas gerais (Overall, For, Against) e o histórico dos últimos 5 jogos
    em casa do mandante e fora do visitante no StatsHub.
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

        # 2. Rola a página para carregar os blocos e tabelas
        driver.execute_script("window.scrollTo(0, 400);")
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

        # 4. EXTRAÇÃO DO HISTÓRICO DE JOGOS (LINHAS TR)
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

                    # Valida se contêm valores numéricos nos gols
                    if data and gols_casa.isdigit() and gols_fora.isdigit():
                        info_jogo = f"{data} | {home_nome} {gols_casa} - {gols_fora} {away_nome}"

                        # Jogos do Mandante jogando em Casa
                        if len(lista_jogos_casa) < 5 and t1.lower() in home_nome.lower():
                            lista_jogos_casa.append(info_jogo)

                        # Jogos do Visitante jogando Fora
                        elif len(lista_jogos_fora) < 5 and t2.lower() in away_nome.lower():
                            lista_jogos_fora.append(info_jogo)
            except Exception:
                continue

    except Exception as e:
        print(f"   ⚠️ Erro durante a raspagem: {e}")

    # LOG ESTRUTURADO NO TERMINAL
    print("\n" + "="*60)
    print("📊 STATSHUB - MÉTRICAS & HISTÓRICO DE JOGOS")
    print("="*60)
    print(f"🏠 {t1} (Casa):")
    print(f"   • Overall : {overall_casa}")
    print(f"   • Marcados (For) : {for_casa}")
    print(f"   • Sofridos (Against) : {against_casa}")
    print("   • Últimos 5 jogos em casa:")
    for j in lista_jogos_casa:
        print(f"     - {j}")

    print("-" * 60)
    print(f"✈️ {t2} (Fora):")
    print(f"   • Overall : {overall_fora}")
    print(f"   • Marcados (For) : {for_fora}")
    print(f"   • Sofridos (Against) : {against_fora}")
    print("   • Últimos 5 jogos fora:")
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
