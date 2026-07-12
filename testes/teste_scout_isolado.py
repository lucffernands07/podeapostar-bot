import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Mantendo a emulação mobile para forçar o layout do seu print
    chrome_options.add_argument("--window-size=412,915") 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    url_jogo = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo"
    
    print("\n🚀 INICIANDO TESTE #30 (CORREÇÃO DE SINTAXE F-STRING + CLIQUE)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a URL base do jogo...")
        driver.get(url_jogo)
        time.sleep(4.0)
        
        print("[PASSO 2] Tentando clicar no botão 'ESTATÍSTICAS DE JOGADOR'...")
        try:
            botao_scout = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'ESTATÍSTICAS DE JOGADOR') or contains(text(), 'ESTATÍSTICAS DE JOGADORES') or contains(text(), 'Jogadores')]")))
            driver.execute_script("arguments[0].click();", botao_scout)
            print("   ✅ Botão clicado via texto!")
            time.sleep(3.0)
        except Exception as e_clique:
            print(f"   ⚠️ Falha no clique por texto puro: {e_clique}")
            print("   🔄 Tentando clicar em qualquer sub-aba de estatísticas disponível...")
            abas = driver.find_elements(By.CSS_SELECTOR, "[class*='tab'], button, a")
            for aba in abas:
                txt_aba = aba.text.strip().upper()
                if "JOGADOR" in txt_aba or "ESTATÍSTICA" in txt_aba:
                    driver.execute_script("arguments[0].click();", aba)
                    print(f"   ✅ Clicou na aba alternativa: '{txt_aba}'")
                    time.sleep(3.0)
                    break

        # [PASSO 3] Validação usando seus seletores confirmados do celular
        jogadores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
        valores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
        
        print(f"\n📊 Resultado pós-clique em ambiente emulado:")
        print(f"   👤 Jogadores identificados: {len(jogadores)}")
        print(f"   🔢 Células numéricas identificadas: {len(valores)}")
        
        if len(jogadores) > 0:
            print("\n📋 Primeiras amostras capturadas:")
            for idx, jog in enumerate(jogadores[:3]):
                # Tratando o texto fora da f-string para evitar o SyntaxError do backslash
                texto_limpo = jog.text.replace('\n', ' | ')
                print(f"   👉 Atleta {idx+1}: {texto_limpo}")

    except Exception as e:
        print(f"\n❌ Erro Geral no Fluxo: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #30")

if __name__ == "__main__":
    rodar_teste_isolado()
    
