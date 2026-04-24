import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def testar_odds_real():
    # Configuração do Driver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Descomente se quiser rodar sem ver o navegador
    driver = webdriver.Chrome(options=options)
    
    # URL que você forneceu
    url = "https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-W8mj7MDD/?mid=lfKIYGgU"
    
    try:
        print(f"🚀 Iniciando teste no jogo: Bétis x Real Madrid")
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # 1. Clicar no botão 'Odds'
        print("🖱️ Tentando clicar na aba 'Odds'...")
        btn_odds = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Odds')]")))
        btn_odds.click()

        # 2. Clicar no botão 'Acima/Abaixo'
        print("🖱️ Tentando clicar em 'Acima/Abaixo'...")
        # Usando o texto para garantir, já que a classe pode mudar
        btn_over_under = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acima/Abaixo')]")))
        btn_over_under.click()
        
        # Pequena pausa para garantir que a tabela de odds carregou após o clique
        time.sleep(3)

        # 3. Localizar a linha do 1.5 e capturar a Odd
        print("🔍 Buscando valor de +1.5 Gols...")
        
        # Aqui buscamos todas as linhas de odds
        linhas_odds = driver.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        encontrou = False
        for linha in linhas_odds:
            if "1.5" in linha.text:
                # O seu seletor de odd 'Acima' geralmente é o primeiro valor de odd da linha
                # Buscamos pelo data-testid que você mapeou
                odds_da_linha = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-oddsValue']")
                
                if len(odds_da_linha) >= 2:
                    odd_acima = odds_da_linha[0].text
                    odd_abaixo = odds_da_linha[1].text
                    print(f"\n✅ SUCESSO!")
                    print(f"📊 Mercado: 1.5 Gols")
                    print(f"📈 Odd ACIMA: {odd_acima}")
                    print(f"📉 Odd ABAIXO: {odd_abaixo}")
                    
                    if float(odd_acima.replace(',', '.')) >= 1.20:
                        print("💰 VALOR: Essa odd passa na sua trava!")
                    else:
                        print("🛑 FILTRO: Odd muito baixa para o seu critério.")
                    
                    encontrou = True
                    break
        
        if not encontrou:
            print("❌ Não foi possível localizar a linha '1.5' na tabela.")

    except Exception as e:
        print(f"⚠️ Erro durante o teste: {e}")
        # Tira um print da tela para debug se der erro
        driver.save_screenshot("erro_teste_real.png")
        print("📸 Screenshot do erro salva como 'erro_teste_real.png'")

    finally:
        print("\n🏁 Teste finalizado. Fechando navegador em 5 segundos...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    testar_odds_real()
