import os
import time
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        return int(re.search(r'Google Chrome (\d+)', output).group(1))
    except: return None

def executar_fluxo_final(url_h2h):
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-popup-blocking")
    
    driver = uc.Chrome(options=options, version_main=get_chrome_version())
    url_final_encontrada = None
    
    try:
        print(f"\n🚀 [PASSO 1] Acessando H2H: {url_h2h}")
        driver.get(url_h2h)
        wait = WebDriverWait(driver, 20)

        print("🔍 [PASSO 2] Aguardando Odds carregarem...")
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-testid='wcl-oddsCell']")))
        time.sleep(3) 

        botoes_odds = driver.find_elements(By.XPATH, "//button[@data-testid='wcl-oddsCell']")
        print(f"🎯 [PASSO 3] Encontrados {len(botoes_odds)} botões. Iniciando cascata de testes (Índices 3 a 6)...")

        # Tenta os índices 3, 4, 5 e 6 em sequência
        for indice in range(3, 7):
            if indice >= len(botoes_odds):
                break
                
            print(f"\n--- 🔄 Tentando Índice [{indice}] ---")
            botao_alvo = botoes_odds[indice]
            aba_original = driver.current_window_handle
            
            # Clique
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", botao_alvo)

            # Espera aba abrir (timeout curto de 5s para ser rápido)
            try:
                WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[-1])
                
                # Validação da URL (máximo 8 segundos por tentativa)
                for _ in range(8):
                    url_atual = driver.current_url
                    if "match-odds" in url_atual:
                        url_final_encontrada = url_atual.split('?')[0]
                        if not url_final_encontrada.endswith('/'):
                            url_final_encontrada += '/'
                        print(f"✨ Sucesso no índice [{indice}]!")
                        break
                    time.sleep(1)
                
                # Se achou a URL, fecha a aba e sai do loop de índices
                if url_final_encontrada:
                    driver.close()
                    driver.switch_to.window(aba_original)
                    break
                else:
                    print(f"❌ Índice [{indice}] não levou ao jogo (URL: {driver.current_url}). Tentando próximo...")
                    driver.close()
                    driver.switch_to.window(aba_original)
            except:
                print(f"⚠️ Índice [{indice}] não abriu nova aba ou travou.")
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(aba_original)

        if url_final_encontrada:
            print(f"\n✅ [RESULTADO] URL FINAL: {url_final_encontrada}")
        else:
            print(f"\n❌ [RESULTADO] Falha total: Nenhum índice (3-6) gerou link válido.")
            print(f"🔗 Link de Segurança: https://www.betano.bet.br/sport/futebol/")

    except Exception as e:
        print(f"❌ Erro no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # OS DOIS JOGOS PARA TESTE
    JOGOS_TESTE = [
        "https://www.flashscore.com.br/jogo/futebol/pachuca-QT16qrtK/toluca-8hiBr2eQ/h2h/total/?mid=jVXBsK2k",
        "https://www.flashscore.com.br/jogo/futebol/avai-rPzY7fWt/novorizontino-4lOgZPQl/h2h/total/?mid=8pNsVvYg"
    ]
    
    for url in JOGOS_TESTE:
        executar_fluxo_final(url)
        print("-" * 50)
        
