import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_odd(driver, id_jogo, mercado_sugerido):
    """
    Navega diretamente para a URL do mercado e captura a odd da Betano.
    """
    # MAPEAMENTO DE URLs DIRETAS
    if "+2.5" in mercado_sugerido or "-4.5" in mercado_sugerido:
        url_alvo = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/acima-abaixo/tempo-regulamentar/"
        tipo = "gols"
    elif "Ambas Marcam" in mercado_sugerido:
        url_alvo = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/ambos-marcam/tempo-regulamentar/"
        tipo = "btts"
    elif "1X" in mercado_sugerido or "2X" in mercado_sugerido:
        url_alvo = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/double-chance/tempo-regulamentar/"
        tipo = "dc"
    else:
        # Padrão: 1X2
        url_alvo = f"https://www.flashscore.com.br/jogo/{id_jogo}/odds/1x2-odds/tempo-regulamentar/"
        tipo = "1x2"

    try:
        print(f"        🌐 Indo para: {url_alvo}")
        driver.get(url_alvo)
        
        # O segredo do seu main: tempo para o JS renderizar as odds
        time.sleep(6) 

        # Espera as linhas da tabela aparecerem
        wait = WebDriverWait(driver, 10)
        linhas = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ui-table__row")))

        for linha in linhas:
            texto_linha = linha.text
            
            # FILTRO POR MERCADO
            alvo_encontrado = False
            if tipo == "gols":
                valor_gols = "4.5" if "-4.5" in mercado_sugerido else "2.5" if "+2.5" in mercado_sugerido else "1.5"
                if valor_gols in texto_linha: alvo_encontrado = True
            else:
                # Para BTTS e Dupla Chance, geralmente a Betano está logo nas primeiras linhas
                if "Betano" in texto_linha or "bet365" in texto_linha: alvo_encontrado = True

            if alvo_encontrado:
                # Pega os valores usando o data-testid que você validou
                odds_elementos = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                
                if odds_elementos:
                    # LÓGICA DE SELEÇÃO DA COLUNA
                    if tipo == "gols":
                        # Acima é o primeiro [0], Abaixo é o segundo [1]
                        idx = 1 if "-" in mercado_sugerido else 0
                        return float(odds_elementos[idx].text.replace(',', '.'))
                    
                    elif tipo == "btts":
                        # Sim é o primeiro [0]
                        return float(odds_elementos[0].text.replace(',', '.'))
                    
                    elif tipo == "dc":
                        # 1X = [0], 12 = [1], 2X = [2]
                        idx = 0 if "1X" in mercado_sugerido else 2
                        return float(odds_elementos[idx].text.replace(',', '.'))

    except Exception as e:
        print(f"        ⚠️ Erro capturando odd: {e}")
        return 0.0

    return 0.0
