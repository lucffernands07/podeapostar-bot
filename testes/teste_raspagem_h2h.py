import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, nome_comp=""):
    """
    Raspa os valores de Overall, For e Against do StatsHub clicando na aba Team Stats via SPAN.
    """
    overall_casa, for_casa, against_casa = "N/A", "N/A", "N/A"
    overall_fora, for_fora, against_fora = "N/A", "N/A", "N/A"

    try:
        driver.get(url_jogo)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # 1. Clique na aba "Team Stats" apontando diretamente para o SPAN
        try:
            aba_team_stats = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Team Stats')]"))
            )
            driver.execute_script("arguments[0].click();", aba_team_stats)
            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Aviso: Falha ao clicar na aba Team Stats: {e}")

        # 2. Rola levemente a página para acionar a renderização dinâmica
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)

        # 3. Localiza os blocos de estatísticas (3 colunas com as estatísticas)
        blocos = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-3')]")

        # Processa Mandante (Lanús)
        if len(blocos) >= 1:
            spans_casa = blocos[0].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_casa) >= 3:
                overall_casa = spans_casa[0].text.strip()
                for_casa = spans_casa[1].text.strip()
                against_casa = spans_casa[2].text.strip()

        # Processa Visitante (Estudiantes)
        if len(blocos) >= 2:
            spans_fora = blocos[1].find_elements(By.XPATH, ".//span[contains(@class, 'font-bebas') or contains(@class, 'tabular-nums')]")
            if len(spans_fora) >= 3:
                overall_fora = spans_fora[0].text.strip()
                for_fora = spans_fora[1].text.strip()
                against_fora = spans_fora[2].text.strip()

    except Exception as e:
        print(f"   ⚠️ Erro durante a raspagem: {e}")

    # LOG NO TERMINAL
    print("\n" + "="*50)
    print("📊 MÉTRICAS DE GOLS (STATSHUB)")
    print("="*50)
    print(f"🏠 {t1} (Casa):")
    print(f"   • Overall : {overall_casa}")
    print(f"   • Marcados (For) : {for_casa}")
    print(f"   • Sofridos (Against) : {against_casa}")
    print("-" * 50)
    print(f"✈️ {t2} (Fora):")
    print(f"   • Overall : {overall_fora}")
    print(f"   • Marcados (For) : {for_fora}")
    print(f"   • Sofridos (Against) : {against_fora}")
    print("="*50 + "\n")

    return {
        "overall_casa": overall_casa,
        "for_casa": for_casa,
        "against_casa": against_casa,
        "overall_fora": overall_fora,
        "for_fora": for_fora,
        "against_fora": against_fora,
        "pular_gols": False
    }
