import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    url_chutes = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas-jogadores/finalizacoes"
    
    print("\n🚀 INICIANDO TESTE #25 (SELETORES CIRÚRGICOS DO SEU CELULAR)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Finalizações...")
        driver.get(url_chutes)
        time.sleep(6.0) 
        
        # 🎯 Buscando diretamente pelo data-testid que você extraiu no celular!
        celulas_jogadores = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
        print(f"📊 Células de jogadores detectadas: {len(celulas_jogadores)}")
        
        print("\n📋 EXTRAINDO SCOUTS POR LINHA COMPLETA:")
        print("-" * 60)
        
        contagem = 0
        for celula in celulas_jogadores:
            try:
                # Extrai o nome do jogador usando a classe exata do seu HTML
                nome_el = celula.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='fp-playerName']")
                nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_el).strip()
                
                # Para pegar os números daquela linha, subimos para o elemento pai (o bloco da linha inteira)
                linha_pai = celula.find_element(By.XPATH, "./..")
                
                # Pegamos todas as células de valor/números irmãs dentro desse mesmo pai
                celulas_valores = linha_pai.find_elements(By.CSS_SELECTOR, "[class*='tableBodyCell_'], [class*='Cell']")
                valores = [c.text.strip() for c in celulas_valores if c.text.strip() and c.text.strip() != nome_jogador]
                
                # Se o método acima não trouxer texto, usamos o text bruto do pai limpando o nome
                if not valores:
                    texto_bruto_pai = linha_pai.text.replace(nome_jogador, "").replace("Atacante", "").replace("Defensor", "").replace("Meio-campista", "").replace("Goleiro", "").replace("Ponta", "").replace("Lateral", "")
                    valores = [v.strip() for v in texto_bruto_pai.split("\n") if v.strip()]

                if nome_jogador:
                    print(f"   👤 Jogador: {nome_jogador:<25} | Números Encontrados: {valores}")
                    contagem += 1
                    
            except Exception as e_linha:
                continue
                
        if contagem == 0:
            print("🚨 O seletor achou os jogadores, mas falhou ao mapear os números laterais.")

    except Exception as e:
        print(f"\n❌ Erro Geral no Teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #25")

if __name__ == "__main__":
    rodar_teste_isolado()
    
