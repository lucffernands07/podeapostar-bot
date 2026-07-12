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
    
    print("\n🚀 INICIANDO TESTE #28 (SINCRONIZAÇÃO MATRIZ DE DADOS COMPLETA)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Finalizações...")
        driver.get(url_chutes)
        time.sleep(6.0) 
        
        # 1. Buscamos todas as linhas ou contêineres principais da tabela
        # Usando a classe de linha que você pescou no elemento: fp-tableRow_d4-E5 -> pegamos o prefixo 'fp-tableRow'
        linhas_tabela = driver.find_elements(By.CSS_SELECTOR, "tr, [class*='table__row_'], [class*='tableRow'], [class*='fp-tableRow']")
        print(f"📊 Total de estruturas de linhas detectadas: {len(linhas_tabela)}")
        
        print("\n📋 MAPEANDO JOGADORES E VALORES DIRETAMENTE:")
        print("-" * 60)
        
        contagem = 0
        for linha in linhas_tabela:
            try:
                # Procura o nome do jogador dentro daquela linha específica usando o seu primeiro achado
                jogador_el = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
                if not jogador_el:
                    continue
                    
                nome_jogador = jogador_el[0].text.split("\n")[0]
                if not nome_jogador or "TODOS" in nome_jogador.upper():
                    continue
                
                # Procura todas as células de valor dentro dessa MESMA linha usando o seu segundo achado!
                celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_44gsS")
                valores = [c.text.strip() for c in celulas_valores if c.text.strip()]
                
                if nome_jogador and valores:
                    print(f"   👤 Jogador: {nome_jogador:<22} | Valores da Linha: {valores}")
                    contagem += 1
            except:
                continue
                
        if contagem == 0:
            print("⚠️ Linhas estruturais vazias. Tentando leitura global de células por proximidade...")
            # Fallback seguro caso o Flashscore separe os blocos em tabelas distintas no modo headless
            jogadores_globais = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
            valores_globais = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
            print(f"   Total de Jogadores: {len(jogadores_globais)} | Total de Valores Numéricos: {len(valores_globais)}")
            
            if len(jogadores_globais) > 0 and len(valores_globais) > 0:
                print("   ✅ Fazendo mapeamento por pareamento de Grid...")
                # Como cada jogador costuma ter um número fixo de colunas (ex: 8 colunas nos seus prints), 
                # dividimos os valores proporcionalmente
                colunas_por_jogador = len(valores_globais) // len(jogadores_globais)
                for idx, jog in enumerate(jogadores_globais[:5]):
                    nome = jog.text.split("\n")[0]
                    inicio = idx * colunas_por_jogador
                    fim = inicio + colunas_por_jogador
                    meus_valores = [v.text.strip() for v in valores_globais[inicio:fim]]
                    print(f"   👤 {nome:<22} | Pareado: {meus_valores}")

    except Exception as e:
        print(f"\n❌ Erro Geral no Teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #28")

if __name__ == "__main__":
    rodar_teste_isolado()
                    
