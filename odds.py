import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_odd(driver, id_jogo, mercado_alvo):
    """
    Entra na aba de odds do jogo e captura o valor do mercado escolhido.
    mercado_alvo pode ser: '1X', '2X', 'Under 4.5', 'BTTS', etc.
    """
    url_odds = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/comparacao-de-odds"
    driver.get(url_odds)
    
    try:
        # Espera as odds carregarem (ajuste o seletor conforme o site)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row"))
        )
        
        # Lógica simplificada: busca o texto da odd baseado no mercado
        # Nota: Aqui você precisará mapear os seletores específicos do Flashscore 
        # para cada tipo de mercado (1x2, Over/Under, etc.)
        
        odds_encontradas = driver.find_elements(By.CSS_SELECTOR, ".oddsValueInner")
        
        if odds_encontradas:
            # Exemplo: pegando a primeira odd disponível para teste
            valor_odd = float(odds_encontradas[0].text.replace(',', '.'))
            return valor_odd
            
    except Exception as e:
        print(f"⚠️ Erro ao capturar odd do jogo {id_jogo}: {e}")
        
    return 0.0

def filtrar_bilhete(driver, lista_sugestoes, odd_minima=1.30):
    """
    Recebe a lista de jogos pré-aprovados e filtra pela odd real.
    """
    print(f"\n⚖️ Filtrando jogos com Odd mínima de {odd_minima}...")
    bilhete_validado = []
    
    for jogo in lista_sugestoes:
        # Pega a odd real do mercado sugerido
        odd_real = capturar_odd(driver, jogo['id'], jogo['mercado'])
        
        if odd_real >= odd_minima:
            jogo['odd_real'] = odd_real
            bilhete_validado.append(jogo)
            print(f"✅ Mantido: {jogo['times']} ({jogo['mercado']}) - Odd: {odd_real}")
        else:
            print(f"🛑 Cortado: {jogo['times']} ({jogo['mercado']}) - Odd: {odd_real} (Muito baixa)")
            
    return bilhete_validado
