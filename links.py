import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_link_direto(driver, time_casa, time_fora):
    """
    Pesquisa o confronto no Google, identifica o link oficial da Betano
    e captura a URL real do evento para o bilhete.
    """
    # Criamos a query focada no mercado brasileiro da Betano
    query = f"betano apostas {time_casa} x {time_fora}"
    url_busca = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    # Guarda a aba onde o robô está trabalhando (Flashscore)
    aba_trabalho = driver.current_window_handle
    
    try:
        # Abre a pesquisa em uma nova aba para não perder o progresso da raspagem
        driver.execute_script(f"window.open('{url_busca}', '_blank');")
        
        # Muda o foco para a aba da pesquisa
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # Espera carregar os resultados orgânicos do Google
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.g")))
        
        # Busca todos os links da página de resultados
        links_encontrados = driver.find_elements(By.TAG_NAME, "a")
        
        for link in links_encontrados:
            href = link.get_attribute("href")
            
            # O link real de um jogo na Betano sempre contém '/match/' ou o ID do evento
            if href and "betano.com/match" in href:
                # Clicamos no link para garantir que a URL final seja capturada (tratando redirects)
                driver.get(href)
                time.sleep(2) # Pequena pausa para o carregamento do mercado
                
                url_final_aposta = driver.current_url
                
                # Fecha a aba de busca e volta para a aba principal
                driver.close()
                driver.switch_to.window(aba_trabalho)
                return url_final_aposta
        
        # Se não achar o link específico, fecha a aba e retorna a busca como fallback
        driver.close()
    except Exception as e:
        print(f"      ⚠️ Erro ao processar link de investimento: {e}")
        try:
            if len(driver.window_handles) > 1:
                driver.close()
        except: pass
    
    # Retorna para a aba original do robô
    driver.switch_to.window(aba_trabalho)
    return url_busca
