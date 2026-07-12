import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Forçamos uma tela ultra-larga para o Flashscore abrir a tabela desktop completa sem esconder colunas
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URL direta usando a estrutura SPA padrão do site
    url_chutes = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA/#/resumo/estatisticas-jogadores/finalizacoes"
    
    print("\n🚀 INICIANDO TESTE COM VIEWPORT EXPANDIDO (MATEI A CHARADA)\n" + "="*60)
    
    try:
        print(f"[PASSO 1] Carregando a página de Finalizações...")
        driver.get(url_chutes)
        time.sleep(5.0) # Tempo extra para carregar os scripts internos da tabela
        
        # 1. Mapeamento de Cabeçalhos de forma agressiva (procurando qualquer tag com texto)
        elementos_topo = driver.find_elements(By.CSS_SELECTOR, "[class*='TableHead'], [class*='tableHead'], th, div")
        
        cabecalhos_textos = []
        indice_chutes = -1
        
        # Vamos descobrir qual posição está o "Total de finalizações" ou "Finalizações no alvo"
        idx_atual = 0
        for el in elementos_topo:
            try:
                txt = el.text.strip()
                if txt and len(txt) < 50 and txt not in cabecalhos_textos:
                    cabecalhos_textos.append(txt)
                    # Procurando os termos exatos que aparecem no seu print
                    if any(x in txt.upper() for x in ["TOTAL DE FINALIZAÇÕES", "FINALIZAÇÕES NO ALVO", "FINALIZAÇÕES"]):
                        if indice_chutes == -1: 
                            indice_chutes = idx_atual
                            print(f"🎯 Coluna Alvo Detectada: '{txt}' no índice virtual {indice_chutes}")
                    idx_atual += 1
            except: pass

        # 2. Captura das linhas de jogadores por seletores genéricos de Grid/Linha do Flashscore
        # Testando tanto seletores clássicos quanto baseados em classes comuns de linha
        linhas = driver.find_elements(By.CSS_SELECTOR, "[class*='row_'], [class*='Row_'], [data-testid*='row'], tr, [class*='playerRow']")
        print(f"\n📊 Linhas brutas encontradas por seletores de estrutura: {len(linhas)}")
        
        # Se falhar, tentamos capturar os blocos de nomes de jogadores diretamente
        jogadores_encontrados = driver.find_elements(By.CSS_SELECTOR, "[class*='playerName'], [class*='playerCell'], [class*='participant']")
        print(f"👤 Elementos contendo nomes de atletas na árvore: {len(jogadores_encontrados)}")
        
        if len(jogadores_encontrados) > 0:
            print("\n📋 Mapeando os primeiros atletas e buscando seus valores de chute:")
            for idx, jog in enumerate(jogadores_encontrados[:5]):
                try:
                    nome_atleta = jog.text.strip()
                    if not nome_atleta or "TODOS" in nome_atleta.upper(): continue
                    
                    # Subimos um nível ou buscamos elementos irmãos para achar os números na mesma linha
                    linha_pai = jog.find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or contains(@class, 'Row') or @data-testid][1] | ./ancestor::tr[1]")
                    celulas = linha_pai.find_elements(By.CSS_SELECTOR, "[class*='Cell'], td, div")
                    
                    valores_linha = [c.text.strip() for c in celulas if c.text.strip()]
                    print(f"   👉 Atleta: {nome_atleta} | Todos os valores da linha: {valores_linha}")
                except Exception as e_linha:
                    print(f"   ⚠️ Erro ao ler linha do atleta {idx}: {e_linha}")
        else:
            print("🚨 Ainda trouxe zero. Vamos cuspir um pedaço estrutural do body:")
            print(driver.find_element(By.TAG_NAME, "body").text[:400])

    except Exception as e:
        print(f"\n❌ Erro Geral no Teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE #22")

if __name__ == "__main__":
    rodar_teste_isolado()
                
