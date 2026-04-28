import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capturar_link_direto(driver, time_casa, time_fora):
    """
    Usa o sistema de busca interna da Betano para encontrar o jogo,
    clica no evento e captura a URL final real.
    """
    # Termo de busca limpo para a Betano
    termo = f"{time_casa} {time_fora}"
    url_busca_betano = f"https://br.betano.com/search?q={termo.replace(' ', '%20')}"
    
    aba_original = driver.current_window_handle
    
    try:
        # Abre a busca direta em nova aba
        driver.execute_script(f"window.open('{url_busca_betano}', '_blank');")
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # Espera o card do evento aparecer no resultado da busca
        # O seletor '.api-event-link' ou '[data-testid="event-card"]' é o padrão da Betano
        wait = WebDriverWait(driver, 12)
        seletor_evento = "a[data-testid='event-card'], .api-event-link, a[class*='event-card']"
        
        # Tenta localizar o primeiro link de evento que apareça
        link_evento = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor_evento)))
        
        # Clica no jogo para abrir a página de mercados completa
        driver.execute_script("arguments[0].click();", link_evento)
        
        # Espera a URL mudar para o padrão de jogo (contendo /futebol/ ou /match/)
        time.sleep(3) 
        url_final = driver.current_url
        
        # Se a URL capturada for a correta (não for mais a de search), retorna ela
        if "/search" not in url_final:
            driver.close()
            driver.switch_to.window(aba_original)
            return url_final
            
    except Exception as e:
        print(f"      ⚠️ Erro ao capturar link Betano para {time_casa}: {e}")
    
    # Se falhar em qualquer etapa, limpa as abas e retorna o link de busca como fallback funcional
    try:
        if len(driver.window_handles) > 1:
            driver.close()
    except: pass
    
    driver.switch_to.window(aba_original)
    # Fallback: Link de busca interna da Betano (melhor que link do Google)
    return url_busca_betano
    
