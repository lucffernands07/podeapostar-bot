import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_overalls(driver, url_jogo, t1, t2):
    driver.get(url_jogo)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)

    # Clica na aba Team Stats para garantir que os cards de gols estejam visíveis
    try:
        btn_team_stats = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Team Stats')] | //div[contains(text(), 'Team Stats')]"))
        )
        driver.execute_script("arguments[0].click();", btn_team_stats)
        time.sleep(2)
    except Exception:
        pass

    # Encontra todos os blocos de estatísticas (3 colunas: Overall, For, Against)
    blocos_goals = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-3')]")

    overall_casa = "N/A"
    for_casa = "N/A"
    against_casa = "N/A"

    overall_fora = "N/A"
    for_fora = "N/A"
    against_fora = "N/A"

    # Processa o bloco do Mandante (primeiro bloco encotrado)
    if len(blocos_goals) >= 1:
        textos = [elem.text.strip() for elem in blocos_goals[0].find_elements(By.XPATH, ".//span") if elem.text.strip()]
        # Procura os valores numéricos correspondentes
        for i, t in enumerate(textos):
            if t.lower() == "overall" and i + 1 < len(textos):
                overall_casa = textos[i + 1]
            elif t.lower() == "for" and i + 1 < len(textos):
                for_casa = textos[i + 1]
            elif t.lower() == "against" and i + 1 < len(textos):
                against_casa = textos[i + 1]

    # Processa o bloco do Visitante (segundo bloco encontrado)
    if len(blocos_goals) >= 2:
        textos = [elem.text.strip() for elem in blocos_goals[1].find_elements(By.XPATH, ".//span") if elem.text.strip()]
        for i, t in enumerate(textos):
            if t.lower() == "overall" and i + 1 < len(textos):
                overall_fora = textos[i + 1]
            elif t.lower() == "for" and i + 1 < len(textos):
                for_fora = textos[i + 1]
            elif t.lower() == "against" and i + 1 < len(textos):
                against_fora = textos[i + 1]

    # IMPRESSÃO DIRETA NO LOG
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
