import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def mesmo_time(nome_busca, nome_tabela):
    """
    Verifica de forma flexível se o nome vindo do site (ex: 'Indep Rivad') 
    corresponde ao time buscado (ex: 'Independiente Rivadavia').
    """
    if not nome_busca or not nome_tabela:
        return False
    nb = nome_busca.lower().strip()
    nt = nome_tabela.lower().strip()
    
    # 1. Verificação de substring direta
    if nb in nt or nt in nb:
        return True
    
    # 2. Comparação por prefixos das palavras (mínimo de 3 letras)
    palavras_busca = [p for p in nb.split() if len(p) >= 3]
    palavras_tabela = [p for p in nt.split() if len(p) >= 3]
    
    for pb in palavras_busca:
        for pt in palavras_tabela:
            if pb[:3] == pt[:3] and (pb in pt or pt in pb or pb[:4] == pt[:4]):
                return True
                
    return False

def pegar_estatisticas_statshub(driver, url_jogo, t1, t2, horario=""):
    """
    Raspa as métricas gerais (Overall, For, Against) e o histórico dos últimos 5 jogos
    de cada time no StatsHub.
    """
    overall_casa, for_casa, against_casa = "N/A", "N/A", "N/A"
    overall_fora, for_fora, against_fora = "N/A", "N/A", "N/A"
    
    lista_jogos_casa = []
    lista_jogos_fora = []

    # Exibe cabeçalho padrão no console
    texto_horario = f" - {horario}" if horario else ""
    print(f"\n🏟️ Jogo: {t1} x {t2}{texto_horario}")
    print(f"🔗 URL: {url_jogo}\n")

    try:
        driver.get(url_jogo)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # 1. Clique Híbrido na aba "Stats dos times" (PT) / "Team Stats" (EN)
        xpath_aba_stats = (
            "//*[(self::span or self::button or self::a or self::div) and ("
            "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'stats dos times') or "
            "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'team stats')"
            ")]"
        )

        try:
            aba_team_stats = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, xpath_aba_stats))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", aba_team_stats)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", aba_team_stats)
            time.sleep(3)
        except Exception as e_click:
            # Fallback via JavaScript caso o clique do Selenium encontre impedimentos
            try:
                driver.execute_script("""
                    let elementos = Array.from(document.querySelectorAll('span, button, a, div'));
                    let alvo = elementos.find(el => {
                        let txt = el.innerText ? el.innerText.toLowerCase() : '';
                        return txt.includes('stats dos times') || txt.includes('team stats');
                    });
                    if (alvo) {
                        alvo.scrollIntoView({block: 'center'});
                        alvo.click();
                    }
                """)
                time.sleep(3)
            except Exception as e_js:
                print(f"   ⚠️ Aviso: Falha ao clicar na aba Team Stats / Stats dos times: {e_click}")

        # 2. Rola a página para renderizar elementos inferiores
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

        # 4. EXTRAÇÃO DOS JOGOS (LINHAS TR)
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

                        # Jogos do Mandante
                        if mesmo_time(t1, home_nome) or mesmo_time(t1, away_nome):
                            if len(lista_jogos_casa) < 5 and info_jogo not in lista_jogos_casa:
                                lista_jogos_casa.append(info_jogo)

                        # Jogos do Visitante
                        if mesmo_time(t2, home_nome) or mesmo_time(t2, away_nome):
                            if len(lista_jogos_fora) < 5 and info_jogo not in lista_jogos_fora:
                                lista_jogos_fora.append(info_jogo)
            except Exception:
                continue

    except Exception as e:
        print(f"   ⚠️ Erro durante a raspagem de {t1} x {t2}: {e}")

    # LOG PADRONIZADO NO TERMINAL
    print("============================================================")
    print("📊 STATSHUB - MÉTRICAS & HISTÓRICO DE JOGOS")
    print("============================================================")
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
