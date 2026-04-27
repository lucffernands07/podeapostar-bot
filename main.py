import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def realizar_teste_h2h_especifico():
    # --- CONFIGURAÇÕES PARA GITHUB ACTIONS ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 25)
    
    # Link principal fornecido
    url_principal = "https://www.flashscore.com.br/jogo/futebol/espanyol-QFfPdh1J/levante-G8FL0ShI/"
    # Forçamos o sufixo do H2H para garantir que o Selenium tente ir direto para a aba correta
    url_alvo = url_principal + "#/h2h/overall"
    
    try:
        print(f"\n🚀 ACESSANDO: {url_alvo}")
        driver.get(url_alvo)

        # 1. Aguarda o carregamento do container H2H
        print("⏳ Aguardando carregamento da estrutura H2H...")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        except:
            print("⚠️ Aba H2H não carregou automaticamente. Tentando atualizar...")
            driver.refresh()
            time.sleep(5)

        # 2. Localizar todas as seções H2H
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        print(f"✅ Total de seções encontradas: {len(secoes)}")

        # 3. Identificar a seção de Confronto Direto pelo título
        secao_direta = None
        for s in secoes:
            try:
                titulo = s.find_element(By.CSS_SELECTOR, ".section__title").text.upper()
                if "CONFRONTOS DIRETOS" in titulo or "H2H" in titulo:
                    secao_direta = s
                    break
            except:
                continue

        if not secao_direta:
            print("❌ ERRO: Seção 'Confrontos Diretos' não encontrada.")
            if len(secoes) >= 3:
                secao_direta = secoes[2]
                print("⚠️ Usando índice [2] como alternativa.")
            else:
                driver.save_screenshot("erro_layout.png")
                return

        # 4. Expandir resultados se necessário
        try:
            btn_mais = secao_direta.find_element(By.CSS_SELECTOR, "span[class*='showMore']")
            driver.execute_script("arguments[0].click();", btn_mais)
            print("➕ Histórico expandido.")
            time.sleep(2)
        except:
            print("ℹ️ Botão de expansão não encontrado.")

        # 5. Extração dos dados
        linhas = secao_direta.find_elements(By.CSS_SELECTOR, ".h2h__row")
        print(f"\n--- ANALISANDO ÚLTIMOS {len(linhas)} JOGOS (H2H) ---")

        vitorias_t1 = 0
        empates = 0

        for i, linha in enumerate(linhas[:6]):
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                # Identificação por Classe CSS (Cor do ícone)
                icones = linha.find_elements(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                resultado = "Indefinido"
                
                if icones:
                    classe = icones[0].get_attribute("class").lower()
                    if 'win' in classe or 'w' in classe:
                        vitorias_t1 += 1
                        resultado = "VITÓRIA ✅"
                    elif 'draw' in classe or 'd' in classe:
                        empates += 1
                        resultado = "EMPATE 🤝"
                    elif 'loss' in classe or 'l' in classe:
                        resultado = "DERROTA ❌"

                print(f"[{i+1}] {casa} {placar} {fora} | Resultado: {resultado}")

            except Exception as e:
                print(f"⚠️ Erro na linha {i+1}: {e}")

        # Resumo final
        total_analisado = i + 1
        taxa_sucesso_1x = ((vitorias_t1 + empates) / total_analisado) * 100
        
        print("\n" + "="*40)
        print(f"📊 RELATÓRIO DE PERFORMANCE H2H:")
        print(f"Jogos: {total_analisado} | Vitórias: {vitorias_t1} | Empates: {empates}")
        print(f"Taxa de Sucesso (1X): {taxa_sucesso_1x:.1f}%")
        print("="*40)

    except Exception as e:
        print(f"❌ Erro crítico durante execução: {e}")
        driver.save_screenshot("debug_github_actions.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
        
