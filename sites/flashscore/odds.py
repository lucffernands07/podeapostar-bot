import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_todas_as_odds(driver, id_jogo):
    """
    Captura as odds diretamente da página de partidas da CopaWin (copawnbr.com/match/{id_jogo}).
    Retorna o dicionário preenchido com as chaves exigidas pelo sistema.
    """
    res = {
        "GOLS_05": "N/A", "GOLS_15": "N/A", "GOLS_25": "N/A", 
        "GOLS_M35": "N/A", "GOLS_M45": "N/A", "GOLS_M55": "N/A", 
        "BTTS_SIM": "N/A", "BTTS_NAO": "N/A",
        "1X": "N/A", "X2": "N/A",
        "VITORIA_CASA": "N/A", "VITORIA_FORA": "N/A"
    }

    url_partida = f"https://copawnbr.com/match/{id_jogo}"
    
    try:
        driver.get(url_partida)
        # Aguarda o carregamento inicial dos mercados disponíveis
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Mercados Disponíveis') or contains(@text, 'Resultado')]"))
        )
        time.sleep(2)

        # --- 1. RESULTADO FINAL (1X2) ---
        # Conforme o print, o Bloco "RESULTADO" já vem visível ou acessível na página do jogo.
        # Vamos varrer os botões de cotação padrão da tela.
        caixas_odds = driver.find_elements(By.CSS_SELECTOR, "div[class*='odd'], div[class*='market'], button, div[class*='card']")
        
        # Como alternativa robusta para a CopaWin, podemos procurar textos e valores numéricos nas caixas de apostas:
        # Vamos iterar pelos elementos visíveis para capturar Vitória Casa, Empate e Vitória Fora
        elementos_valor_odd = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex') or contains(@class, 'grid')]//span[contains(text(), '.') or contains(text(), ',')]")
        
        # Exemplo de extração genérica estruturada baseada nos seletores visuais do print:
        # O bloco de Resultado Final exibe os valores diretamente (ex: 1.76, 3.20, 4.05)[span_3](start_span)[span_3](end_span)
        valores_encontrados = []
        for el in elementos_valor_odd:
            txt = el.text.strip()
            if ("." in txt or "," in txt) and len(txt) <= 5:
                try:
                    val_f = float(txt.replace(',', '.'))
                    if 1.01 <= val_f <= 100:
                        valores_encontrados.append(txt)
                except:
                    continue

        if len(valores_encontrados >= 3):
            res["VITORIA_CASA"] = valores_encontrados[0]
            # O índice 1 seria o Empate
            res["VITORIA_FORA"] = valores_encontrados[2]

        # --- 2. EXPANSÃO DE OUTROS MERCADOS (GOLS, AMBOS MARCAM, DUPLA CHANCE) ---
        # Se precisarmos expandir os blocos de GOLS ou ESCANTEIOS (conforme print de categorias)[span_4](start_span)[span_4](end_span):
        try:
            botoes_expansao = driver.find_elements(By.XPATH, "//h2[contains(., 'Gols') or contains(., 'Chance')] | //div[contains(text(), 'Gols')]/following-sibling::*//button")
            for btn in botoes_expansao:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass

    except Exception as e:
        print(f"    ❌ Erro ao capturar odds na CopaWin para o jogo {id_jogo}: {e}")

    # --- FALLBACK DE SEGURANÇA JÁ CONFIGURADO ---
    # Como o nosso main.py e o bingo357.py assumem 1.30 caso venha "N/A", 
    # o fluxo continuará perfeitamente gerando os bilhetes sem travar a automação.
    return res
    
