import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_url_betano(driver):
    """
    Extrai a URL real da Betano tentando os índices 3, 4 e 5.
    Descarta links de promoções e retorna None para usar o link genérico se falhar.
    """
    try:
        # 1. Espera os botões carregarem (máximo 8 segundos)
        wait = WebDriverWait(driver, 8)
        botoes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-testid='wcl-oddsCell']")))
        
        aba_original = driver.current_window_handle
        url_final = None

        # 2. Tenta a triade da Betano (Casa, Empate, Fora)
        for i in [3, 4, 5]:
            if i >= len(botoes):
                break
            
            botao_alvo = botoes[i]
            
            # Scroll e clique
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
            time.sleep(0.4) # Pequena pausa para garantir o scroll
            driver.execute_script("arguments[0].click();", botao_alvo)

            try:
                # 3. Espera abertura da nova aba (máximo 4s)
                WebDriverWait(driver, 4).until(lambda d: len(d.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[-1])
                
                # 4. Verificação rápida da URL (checagem a cada 0.5s)
                for _ in range(12): 
                    url_atual = driver.current_url
                    
                    # SUCESSO: É o link do jogo e não é promoção
                    if "match-odds" in url_atual and "promos" not in url_atual:
                        url_final = url_atual.split('?')[0]
                        if not url_final.endswith('/'):
                            url_final += '/'
                        break
                    
                    # REJEIÇÃO: Se cair em link de bônus/promo, para de esperar e fecha
                    if "promos.betano" in url_atual:
                        break
                        
                    time.sleep(0.5)

                # Fecha a aba da Betano e volta para a do Flashscore
                driver.close()
                driver.switch_to.window(aba_original)
                
                # Se encontrou a URL, sai do loop de índices
                if url_final:
                    break
                    
            except:
                # Se algo travar na aba, limpa e tenta o próximo índice
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(aba_original)

        # Retorna a URL (ou None se falhou nos 3 índices)
        return url_final

    except Exception as e:
        print(f"❌ Erro na extração de links: {e}")
        # Garante que o driver volta para a aba principal em caso de erro crítico
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[0])
        return None
        
