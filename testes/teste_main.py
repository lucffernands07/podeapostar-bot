import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# URL enviada (Aba H2H Total do confronto)
URL_H2H_ALVO = "https://www.flashscore.com.br/jogo/futebol/noruega-8rP6JO0H/senegal-hOIsJLJr/h2h/total/"

driver = webdriver.Chrome() # Ajuste para o seu driver/opções se necessário
driver.maximize_window()
wait = WebDriverWait(driver, 10)

# Estrutura para simular o dicionário 'stats' do seu bot
stats_simulado = {
    "historico_mandante_am": {},
    "historico_mandante_vm": {},
    "historico_chutes": {}
}

try:
    print("🔋 [PASSO 1] Acessando a página H2H para listar os confrontos...")
    driver.get(URL_H2H_ALVO)
    
    # Aguarda as linhas de confronto carregarem
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
    
    # Captura as primeiras linhas da primeira seção (Ex: Últimos jogos do Mandante)
    linhas_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
    print(f"👉 Encontrados {len(linhas_h2h)} jogos históricos no H2H do Mandante.")

    # Vamos simular a raspagem entrando no primeiro jogo da lista para testar a transição
    if not linhas_h2h:
        print("❌ Nenhuma linha H2H encontrada para prosseguir o teste.")
        driver.quit()
        exit()

    elemento_jogo = linhas_h2h[0]
    partes_texto = elemento_jogo.text.split('\n')
    print(f"🏟️ Jogo selecionado para o teste: {' '.join(partes_texto[:4])}")
    
    # Clica para abrir o detalhe do jogo histórico
    driver.execute_script("arguments[0].click();", elemento_jogo)
    time.sleep(2)
    
    # Trata se abriu em nova aba ou na mesma janela
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[1])

    # Limpa a URL para remover parâmetros adicionais e focar na raiz do jogo
    url_jogo_base = driver.current_url.split("?")[0].strip("/")
    if "#" in url_jogo_base:
        url_jogo_base = url_jogo_base.split("#")[0].strip("/")
        
    print(f"🔗 URL Base do jogo histórico detectada: {url_jogo_base}")

    # =========================================================================
    # RASPAGEM DE SCOUTS AVANÇADOS (O CORAÇÃO DO PROBLEMA)
    # =========================================================================
    
    # 🗂️ SUB-PASSO A: CARTOES (Aba Gerais de Jogadores)
    url_gerais = f"{url_jogo_base}/resumo/estatisticas-jogadores/gerais/"
    print(f"\n🃏 [PASSO 2.1] Acessando Aba de Cartões: {url_gerais}")
    driver.get(url_gerais)
    
    # Espera crucial: Aguarda uma célula de jogador ou linha da tabela estar visível
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
    time.sleep(1.5) # Respiro para o JS renderizar os números iniciais
    
    # Simulação de leitura de dados de cartões (Apenas para validação no terminal)
    linhas_jogadores_cartoes = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
    print(f"✅ Aba de Cartões pronta! Encontradas {len(linhas_jogadores_cartoes)} linhas de dados.")
    
    # Guardamos o texto do primeiro valor de célula para usar como trava na transição
    texto_trava_antigo = ""
    try:
        celula_dados = driver.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
        texto_trava_antigo = celula_dados.text.strip()
        print(f"🔒 Valor de controle armazenado (Aba Cartões): '{texto_trava_antigo}'")
    except:
        pass

    # 🎯 SUB-PASSO B: CHUTES NO ALVO (Aba Finalizações de Jogadores)
    url_finalizacoes = f"{url_jogo_base}/resumo/estatisticas-jogadores/finalizacoes/"
    print(f"\n🎯 [PASSO 2.2] Mudando para Aba de Chutes no Alvo: {url_finalizacoes}")
    driver.get(url_finalizacoes)
    
    print("🛡️ [BLINDAGEM] Aguardando o Flashscore limpar os dados antigos e renderizar os novos...")
    
    # 🚀 AQUI ACONTECE A MÁGICA: Espera até que o elemento saia do estado da aba anterior
    if texto_trava_antigo:
        try:
            wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != texto_trava_antigo)
            print("🔄 [SINCRO] Sucesso! O DOM detectou a mudança nos números das colunas.")
        except Exception as e_timeout:
            print("⚠️ Aviso: O valor da primeira célula não mudou (pode ser o mesmo número ou a tabela demorou).")
    else:
        # Fallback se a trava estava vazia: espera até que as células tenham conteúdo preenchido
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != "")

    time.sleep(1.0) # Pequena margem de segurança milimétrica para acomodar a tabela inteira

    # Coleta de Chutes no Alvo atualizada
    linhas_jogadores_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
    print(f"✅ Aba de Finalizações sincronizada com sucesso! Total de linhas: {len(linhas_jogadores_fin)}")
    
    # Mostra os 5 primeiros jogadores com os dados atualizados da nova aba
    print("\n📊 --- EXTRATO DOS PRIMEIROS JOGADORES NA ABA FINALIZAÇÕES ---")
    contagem_amostra = 0
    for linha in lines_jogadores_fin:
        try:
            nome = linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName']").text.strip()
            if not nome or "TODOS" in nome.upper() or "JOGADOR" in nome.upper():
                continue
            
            # Pega todas as colunas de dados da linha atual
            valores = [td.text.strip() for td in linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")]
            print(f"🏃‍♂️ Atleta: {nome} | Colunas de Dados: {valores}")
            
            contagem_amostra += 1
            if contagem_amostra >= 5:
                break
        except:
            continue

except Exception as e_geral:
    print(f"❌ Erro crítico no fluxo de execução do teste: {e_geral}")

finally:
    print("\n🏁 Fim do teste integrado. Fechando instâncias do navegador.")
    driver.quit()
