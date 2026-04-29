import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_url_betano(driver):
    """
    Função principal que será chamada pelo main.py.
    Ela assume que o driver já está na página H2H do jogo.
    """
    try:
        # 1. Localiza os botões de odds na página atual
        # Usamos o data-testid que validamos no teste
        botoes = driver.find_elements(By.XPATH, "//button[@data-testid='wcl-oddsCell']")
        
        if len(botoes) >= 4:
            # O 4º botão (índice 3) é o primeiro da segunda casa (Betano)
            botao_alvo = botoes[3]
            
            # 2. Dispara o clique forçado via JavaScript
            driver.execute_script("arguments[0].click();", botao_alvo)
            
            # 3. Gerencia a troca de abas
            aba_original = driver.current_window_handle
            
            # Espera até 15 segundos para a nova aba abrir
            WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
            
            # Muda para a aba da Betano (a última aberta)
            driver.switch_to.window(driver.window_handles[-1])
            
            # 4. Captura e limpa a URL
            url_final = ""
            for _ in range(25): # Tolerância para redirecionamentos lentos
                url_atual = driver.current_url
                if "match-odds" in url_atual:
                    # Aplica a limpeza que validamos
                    url_final = url_atual.split('?')[0]
                    if not url_final.endswith('/'):
                        url_final += '/'
                    break
                time.sleep(1)
            
            # 5. Fecha a aba da Betano e volta para a aba do Flashscore
            driver.close()
            driver.switch_to.window(aba_original)
            
            return url_final
            
        else:
            print("⚠️ Odds da Betano não encontradas nesta página.")
            return None

    except Exception as e:
        print(f"❌ Erro ao processar link Betano: {e}")
        # Garante que volta para a aba original se algo der errado
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[0])
        return None
        
