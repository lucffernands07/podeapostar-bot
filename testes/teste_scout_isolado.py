import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Voltamos para a tela gigante que abriu o DOM com sucesso no teste retrasado
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URL alvo direta para a rota de estatísticas
    url_chutes = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas-jogadores/finalizacoes"
    
    print("\n🚀 INICIANDO TESTE #31 (FORÇAR ROTA DESKTOP VIA JAVASCRIPT CORRETO)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Forçando o carregamento direto da rota...")
        driver.get(url_chutes)
        time.sleep(6.0) # Tempo maior para o script interno montar os blocos congelados
        
        # Como o site separa a coluna congelada dos valores, buscamos as células de forma global
        # usando os dois data-testids idênticos aos que você confirmou no celular!
        jogadores_globais = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
        valores_globais = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
        
        print(f"\n📊 Resultado da varredura direta:")
        print(f"   👤 Elementos de jogadores encontrados: {len(jogadores_globais)}")
        print(f"   🔢 Elementos de valores numéricos encontrados: {len(valores_globais)}")
        
        if len(jogadores_globais) > 0:
            print("\n📋 MAPEAMENTO POR PAREAMENTO DE MATRIZ DE SCROLL:")
            print("-" * 60)
            
            # Como vimos no seu print, existem colunas numéricas sequenciais para cada linha de atleta.
            # Vamos calcular dinamicamente a proporção de células numéricas por jogador:
            colunas_por_jogador = len(valores_globais) // len(jogadores_globais) if len(jogadores_globais) > 0 else 0
            print(f"   ℹ️ Colunas numéricas detectadas por atleta: {colunas_por_jogador}\n")
            
            for idx, jog in enumerate(jogadores_globais[:10]):
                try:
                    nome = jog.text.split("\n")[0]
                    if not nome or "TODOS" in nome.upper(): continue
                    
                    # Fatiamos o array de valores correspondente ao índice do jogador na tela
                    inicio = idx * colunas_por_jogador
                    fim = inicio + colunas_por_jogador
                    meus_valores = [v.text.strip() for v in valores_globais[inicio:fim] if v.text.strip()]
                    
                    print(f"   👤 {nome:<22} | Valores coletados: {meus_valores}")
                except Exception as e_print:
                    print(f"   ⚠️ Erro ao parear índice {idx}: {e_print}")
        else:
            print("\n🔄 Tentativa de Fallback agressiva: Buscando por classes derivadas...")
            jogadores_classe = driver.find_elements(By.CSS_SELECTOR, "[class*='playerCell']")
            valores_classe = driver.find_elements(By.CSS_SELECTOR, "[class*='tableBodyCell']")
            print(f"   👤 Por classe (jogadores): {len(jogadores_classe)}")
            print(f"   🔢 Por classe (valores): {len(valores_classe)}")

    except Exception as e:
        print(f"\n❌ Erro Geral no Teste: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE #31")

if __name__ == "__main__":
    rodar_teste_isolado()
    
