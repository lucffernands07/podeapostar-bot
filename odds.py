import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_odd(driver, id_jogo, mercado_sugerido):
    """
    Navega para a aba correta e captura a odd da Betano/Bet365.
    """
    url_base = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/comparacao-de-odds"
    
    try:
        # 1. IDENTIFICA A SUB-ABA CORRETA
        if "+2.5" in mercado_sugerido or "-4.5" in mercado_sugerido:
            driver.get(url_base + "/acima-abaixo")
            tipo = "gols"
        elif "Ambas Marcam" in mercado_sugerido or "btts" in mercado_sugerido.lower():
            driver.get(url_base + "/ambos-marcam")
            tipo = "btts"
        elif "1X" in mercado_sugerido or "2X" in mercado_sugerido:
            driver.get(url_base + "/dupla-chance")
            tipo = "dc"
        else:
            # Caso seja o mercado principal (1X2)
            driver.get(url_base + "/1x2-odds")
            tipo = "1x2"

        # Aguarda as odds carregarem
        WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        
        # 2. LOCALIZA A LINHA DA BETANO (ou Bet365 se Betano não houver)
        # Usando o alt da imagem para identificar a casa de aposta conforme seus prints
        try:
            linha_casa = driver.find_element(By.XPATH, "//img[contains(@alt, 'Betano')]/ancestor::div[contains(@class, 'ui-table__row')]")
        except:
            linha_casa = driver.find_element(By.XPATH, "//img[contains(@alt, 'bet365')]/ancestor::div[contains(@class, 'ui-table__row')]")

        odds = linha_casa.find_elements(By.CSS_SELECTOR, ".oddsValueInner")

        # 3. EXTRAI O VALOR BASEADO NA COLUNA
        if tipo == "gols":
            if "+2.5" in mercado_sugerido:
                # Na linha do 2.5, coluna 'Acima' (geralmente a primeira odd da célula)
                # O Flashscore agrupa por linhas (1.5, 2.5, 3.5...). 
                # Se houver várias linhas, precisamos filtrar a correta:
                linha_especifica = driver.find_element(By.XPATH, "//div[contains(text(), '2.5')]/ancestor::div[contains(@class, 'ui-table__row')]")
                odd_val = linha_especifica.find_element(By.XPATH, ".//img[contains(@alt, 'Betano')]/../..//span").text
                return float(odd_val.replace(',', '.'))
            
            elif "-4.5" in mercado_sugerido:
                # Procura a linha 4.5 e pega a odd da direita (Abaixo)
                return float(odds[1].text.replace(',', '.'))

        elif tipo == "btts":
            # Primeira coluna é 'Sim', segunda é 'Não'
            return float(odds[0].text.replace(',', '.'))

        elif tipo == "dc":
            if "1X" in mercado_sugerido: return float(odds[0].text.replace(',', '.'))
            if "12" in mercado_sugerido: return float(odds[1].text.replace(',', '.'))
            if "2X" in mercado_sugerido: return float(odds[2].text.replace(',', '.'))

    except Exception as e:
        print(f"    ⚠️ Erro ao capturar odd ({mercado_sugerido}): {e}")
        return 0.0

    return 0.0
