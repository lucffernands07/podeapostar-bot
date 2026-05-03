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
        # Espera carregar os botões de odd específicos
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-testid='wcl-oddsCell']")))
        time.sleep(3) 

        botoes_odds = driver.find_elements(By.XPATH, "//button[@data-testid='wcl-oddsCell']")
        print(f"🎯 [PASSO 3] Encontrados {len(botoes_odds)} botões. Iniciando busca persistente (Índices 3 a 10)...")

        # Tentamos do índice 3 ao 10 para pular as "Odds Turbinadas" (Promos)
        for indice in range(3, 11):
            if indice >= len(botoes_odds):
                break
                
            print(f"\n--- 🔄 Testando Índice [{indice}] ---")
            botao_alvo = botoes_odds[indice]
            aba_original = driver.current_window_handle
            
            # Tenta ler o valor da odd para o log
            try:
                valor_odd = botao_alvo.text.splitlines()[0]
                print(f"📊 Valor da Odd neste botão: {valor_odd}")
            except: pass

            # Executa o clique
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", botao_alvo)

            try:
                # Espera a aba abrir (máximo 5s para não atrasar o robô)
                WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[-1])
                
                # Monitora a URL por 8 segundos (tempo para o redirecionamento da Betano)
                for _ in range(8):
                    url_atual = driver.current_url
                    
                    # CRITÉRIO DE SUCESSO: Tem que ter match-odds e NÃO pode ser link de promo
                    if "match-odds" in url_atual and "promos" not in url_atual:
                        url_final_encontrada = url_atual.split('?')[0]
                        if not url_final_encontrada.endswith('/'):
                            url_final_encontrada += '/'
                        break
                    
                    # Se detectou que caiu em promoção, já cancela essa tentativa
                    if "promos.betano" in url_atual:
                        print("⚠️ Detectado link de Promoção. Descartando...")
                        break
                        
                    time.sleep(1)
                
                # Se achou a URL real do jogo, encerra a busca
                if url_final_encontrada:
                    print(f"✨ SUCESSO NO ÍNDICE [{indice}]!")
                    driver.close()
                    driver.switch_to.window(aba_original)
                    break
                else:
                    print(f"❌ Índice [{indice}] falhou (URL atual: {driver.current_url[:50]}...)")
                    driver.close()
                    driver.switch_to.window(aba_original)
                    
            except Exception as e:
                print(f"⚠️ Erro ao processar aba no índice [{indice}]")
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(aba_original)

        if url_final_encontrada:
            print(f"\n✅ [FINAL] URL CAPTURADA: {url_final_encontrada}")
        else:
            print(f"\n❌ [FINAL] Não foi possível capturar link direto nos índices testados.")
            print(f"🔗 Link de Backup: https://www.betano.bet.br/sport/futebol/")

    except Exception as e:
        print(f"❌ Erro crítico no fluxo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # URLs de teste: Toluca (difícil/promo) e Avaí (fácil/direto)
    LISTA_H2H = [
        "https://www.flashscore.com.br/jogo/futebol/pachuca-QT16qrtK/toluca-8hiBr2eQ/h2h/total/?mid=jVXBsK2k",
        "https://www.flashscore.com.br/jogo/futebol/avai-rPzY7fWt/novorizontino-4lOgZPQl/h2h/total/?mid=8pNsVvYg"
    ]
    
    for url in LISTA_H2H:
        executar_fluxo_final(url)
        print("\n" + "="*60 + "\n")
            
