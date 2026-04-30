import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_url_betano(driver):
    """
    Extrai o link real da Betano usando o índice [4] para pular 
    banners promocionais e garantir a captura do ID da partida.
    """
    try:
        # 1. Espera os botões de odds carregarem
        wait = WebDriverWait(driver, 10)
        botoes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-testid='wcl-oddsCell']")))
        
        # 2. Validação: Precisamos de pelo menos 5 botões para acessar o índice [4]
        if len(botoes) >= 5:
            # O índice [4] pula a 1ª casa e o banner promocional (que é o [3] no Vasco)
            botao_alvo = botoes[4]
            
            # Garante que o botão está na tela antes de clicar
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
            time.sleep(1)
            
            # 3. Clique forçado via JS para evitar erros de interposição
            driver.execute_script("arguments[0].click();", botao_alvo)
            
            # 4. Gerenciamento de abas
            aba_original = driver.current_window_handle
            WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[-1])
            
            # 5. Captura da URL com filtro anti-promoção
            url_final = ""
            for _ in range(25): # Tolerância para redirecionamentos lentos
                url_atual = driver.current_url
                # Se for o link real da partida (match-odds) e não for lixo promocional
                if "betano" in url_atual and "match-odds" in url_atual and "promos" not in url_atual:
                    url_final = url_atual.split('?')[0]
                    if not url_final.endswith('/'):
                        url_final += '/'
                    break
                time.sleep(1)
            
            # 6. Fecha a aba da Betano e retorna à aba do Flashscore
            driver.close()
            driver.switch_to.window(aba_original)
            
            return url_final if url_final else None
            
        else:
            print(f"⚠️ Botões insuficientes para o índice [4] (Encontrados: {len(botoes)})")
            return None

    except Exception as e:
        print(f"❌ Erro ao processar link no índice [4]: {e}")
        # Recuperação: volta para a aba original se algo travar
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[0])
        return None
        
