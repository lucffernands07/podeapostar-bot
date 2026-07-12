import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Mantendo o tamanho de tela que trouxe os dados com sucesso
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    url_chutes = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas-jogadores/finalizacoes"
    
    print("\n🚀 INICIANDO TESTE FINAL DE EXTRAÇÃO DE DADOS POR LINHA\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Finalizações...")
        driver.get(url_chutes)
        time.sleep(5.0) 
        
        # 1. Buscando as linhas de dados válidas da tabela pelo padrão 'wcl-table__row_' ou 'wcl-tableRow'
        linhas = driver.find_elements(By.CSS_SELECTOR, "[class*='table__row_'], [class*='tableRow'], tr")
        print(f"📊 Linhas de tabela identificadas no DOM: {len(linhas)}")
        
        print("\n📋 LENDO DADOS DOS JOGADORES DIRETAMENTE DA ESTRUTURA:")
        print("-" * 60)
        
        contagem_sucessos = 0
        for idx, linha in enumerate(linhas):
            try:
                # Pegamos todo o texto contido dentro daquela linha específica
                texto_linha = linha.text.strip()
                
                # Ignora linhas vazias ou o cabeçalho principal da tabela
                if not texto_linha or "TOTAL DE" in texto_linha.upper() or "GOLS" in texto_linha.upper():
                    continue
                
                # Extrai o nome do jogador buscando a classe de nome dentro desta linha específica
                nome_el = linha.find_elements(By.CSS_SELECTOR, "[class*='playerName'], [class*='playerCell'], [class*='participant']")
                if not nome_el:
                    continue
                nome_jogador = nome_el[0].text.strip()
                
                # Captura todas as células de valores/números presentes nesta linha
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [class*='tableBodyCell_'], [class*='Cell']")
                valores = [c.text.strip() for c in celulas if c.text.strip()]
                
                # Como a primeira coluna numérica após o nome/posição costuma ser o "Total de Finalizações"
                # (conforme vimos no seu primeiro print), vamos listar todos para garantir
                if nome_jogador and valores:
                    print(f"   👤 Jogador: {nome_jogador:<20} | Dados extraídos da linha: {valores}")
                    contagem_sucessos += 1
                    
            except Exception as e_linha:
                # Passa silenciosamente se encontrar alguma linha de propaganda ou divisão interna
                continue
                
        if contagem_sucessos == 0:
            print("⚠️ Nenhuma linha pôde ser processada. Estrutura do texto bruto da primeira linha encontrada:")
            if linhas: print(f"👉 {linhas[0].text}")

    except Exception as e:
        print(f"\n❌ Erro Geral no Teste: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE #23")

if __name__ == "__main__":
    rodar_teste_isolado()
                
