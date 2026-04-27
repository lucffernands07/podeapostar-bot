import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def realizar_teste_h2h_especifico():
    # --- CONFIGURAÇÕES PARA GITHUB ACTIONS (SERVER SIDE) ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # OBRIGATÓRIO NO GITHUB
    chrome_options.add_argument("--no-sandbox") # OBRIGATÓRIO NO GITHUB
    chrome_options.add_argument("--disable-dev-shm-usage") # EVITA CRASH DE MEMÓRIA
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    id_jogo = "QFfPdh1J" # Espanyol x Levante
    url_h2h = f"https://www.flashscore.com.br/jogo/{id_jogo}/#/h2h/overall"
    
    try:
        print(f"\n🚀 ACESSANDO: {url_h2h}")
        driver.get(url_h2h)
        time.sleep(8) # Tempo maior para o GitHub processar os scripts da página

        # Localizar as seções de H2H
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        if len(secoes) < 3:
            print("❌ ERRO: Terceira seção (Confronto Direto) não encontrada.")
            return

        confronto_direto = secoes[2]
        print(f"✅ Seção 'Confronto Direto' identificada.")

        # Tenta expandir a lista
        try:
            btn_mais = confronto_direto.find_element(By.CSS_SELECTOR, "span[class*='showMore']")
            driver.execute_script("arguments[0].click();", btn_mais)
            print("➕ Expandindo histórico...")
            time.sleep(3)
        except:
            print("ℹ️ Botão 'Mostrar mais' não disponível ou já expandido.")

        linhas = confronto_direto.find_elements(By.CSS_SELECTOR, ".h2h__row")
        print(f"\n--- ANALISANDO ÚLTIMOS {len(linhas)} CONFRONTOS DIRETOS ---")

        vitorias_casa = 0
        empates = 0
        derrotas_casa = 0

        for i, linha in enumerate(linhas[:6]): # Analisa até os últimos 6 jogos
            try:
                casa = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text
                fora = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text
                placar = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                
                # IDENTIFICAÇÃO PELA CLASSE CSS (COR) - SOLUÇÃO PARA FALTA DE LETRAS
                icones = linha.find_elements(By.CSS_SELECTOR, "span[class*='h2h__icon']")
                resultado_final = "Indefinido"
                
                if icones:
                    # Capturamos o nome da classe CSS do ícone
                    classe = icones[0].get_attribute("class").lower()
                    
                    # No Flashscore: 'win' (verde), 'draw' (amarelo), 'loss' (vermelho)
                    if 'win' in classe or 'w' in classe:
                        vitorias_casa += 1
                        resultado_final = "VITÓRIA ✅"
                    elif 'draw' in classe or 'd' in classe:
                        empates += 1
                        resultado_final = "EMPATE 🤝"
                    elif 'loss' in classe or 'l' in classe:
                        derrotas_casa += 1
                        resultado_final = "DERROTA ❌"

                print(f"Jogo {i+1}: {casa} {placar} {fora} | Classe Capturada: '{classe.split()[-1]}' | Resultado: {resultado_final}")

            except Exception as e:
                print(f"⚠️ Erro ao processar linha {i+1}: {e}")

        # RESUMO PARA DECISÃO DO FILTRO
        total = i + 1
        taxa_1x = ((vitorias_casa + empates) / total) * 100
        
        print("\n" + "="*40)
        print("📊 RELATÓRIO FINAL DO H2H:")
        print(f"Total de jogos analisados: {total}")
        print(f"Vitórias T1: {vitorias_casa}")
        print(f"Empates: {empates}")
        print(f"Taxa de Sucesso (1X): {taxa_1x:.1f}%")
        print("="*40)
        
        if taxa_1x >= 80:
            print("🚀 O jogo PASSARIA no filtro de 1X (4/5 ou 5/6)")
        else:
            print("🛑 O jogo SERIA BARRADO pelo filtro atual.")

    except Exception as e:
        print(f"❌ Erro crítico no teste: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_teste_h2h_especifico()
