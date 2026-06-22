import os
import time
import re
import requests
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =========================================================================
# CONFIGURAÇÃO DO DRIVER ORIGINAL DO SEU MAIN.PY
# =========================================================================
def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30) 
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "UTC"})
    return driver

# =========================================================================
# SCRIPT DE EXECUÇÃO DO TESTE INTEGRADO DE RASPAGEM
# =========================================================================
if __name__ == "__main__":
    # URL do H2H Alvo enviada por você
    URL_H2H_ALVO = "https://www.flashscore.com.br/jogo/futebol/noruega-8rP6JO0H/senegal-hOIsJLJr/h2h/total/"
    t1, t2 = "Noruega", "Senegal"

    print("🚀 Inicializando driver com as configurações do main.py...")
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)

    stats = {
        "historico_mandante_am": {}, "historico_mandante_vm": {},
        "historico_visitante_am": {}, "historico_visitante_vm": {},
        "historico_chutes": {}
    }

    try:
        print(f"🔋 [RASPAGEM 1] Acessando aba H2H: {URL_H2H_ALVO}")
        driver.get(URL_H2H_ALVO)
        
        # Sincroniza o carregamento inicial da listagem
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # Captura as linhas dos jogos anteriores do mandante (Noruega)
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
        print(f"✅ Sucesso! Encontrados {len(linhas_confrontos)} confrontos históricos no painel.")

        if len(linhas_confrontos) == 0:
            print("❌ Nenhuma linha de confronto localizada.")
            driver.quit()
            exit()

        # Seleciona o primeiro jogo da lista para simular a abertura
        elemento_jogo = linhas_confrontos[0]
        texto_jogo = elemento_jogo.text.replace('\n', ' ')
        print(f"🏟️ Abrindo jogo histórico: {texto_jogo}")

        # Executa o clique simulando a abertura do sub-painel de jogo
        driver.execute_script("arguments[0].click();", elemento_jogo)
        time.sleep(3)

        # Se abrir em uma nova janela/aba do navegador, altera o foco
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # Limpa e formata a URL base do jogo selecionado
        url_jogo_completa = driver.current_url.split("?")[0].split("#")[0].strip("/")
        print(f"🔗 URL Base do Jogo de Scout Detectada: {url_jogo_completa}")

        # -----------------------------------------------------------------
        # 🗂️ SUB-PASSO A: RASPAGEM DE CARTÕES (ABA GERAIS)
        # -----------------------------------------------------------------
        url_gerais = f"{url_jogo_completa}/resumo/estatisticas-jogadores/gerais/"
        print(f"\n🃏 [RASPAGEM 2.1] Entrando na Aba Gerais (Cartões): {url_gerais}")
        driver.get(url_gerais)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
        time.sleep(1.5) # Tempo técnico para fixação do DOM
        
        # Captura uma amostra textual de segurança para servir de trava de estado anterior
        texto_trava_antigo = ""
        try:
            celula_dados = driver.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
            texto_trava_antigo = driver.execute_script("return arguments[0].textContent;", celula_dados).strip()
            print(f"🔒 Valor de controle registrado na Aba Cartões: '{texto_trava_antigo}'")
        except Exception as e_trava:
            print(f"⚠️ Erro ao registrar controle: {e_trava}")

        # -----------------------------------------------------------------
        # 🎯 SUB-PASSO B: RASPAGEM DE CHUTES NO ALVO (ABA FINALIZAÇÕES)
        # -----------------------------------------------------------------
        url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"\n🎯 [RASPAGEM 2.2] Modificando para Aba Finalizações: {url_finalizacoes}")
        driver.get(url_finalizacoes)
        
        print("🛡️ [BLINDAGEM] Sincronizando transição de estado da tabela...")
        
        # Aplicação da trava: o script só avança se o primeiro número mudar ou se a tabela atualizar por completo
        if texto_trava_antigo:
            try:
                wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != texto_trava_antigo)
                print("🔄 [SINCRO] Sucesso! O navegador identificou a mudança de dados da sub-aba.")
            except:
                print("⚠️ Aviso: Tempo limite da trava atingido. Proseguindo com validação secundária.")
        else:
            wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != "")

        time.sleep(1.2) # Margem milimétrica de assentamento do DOM no GitHub Actions

        # Leitura analítica das linhas finais de finalizações atualizadas
        linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
        print(f"📊 Total de linhas identificadas na tabela final: {len(linhas_dados_fin)}")
        
        print("\n📝 --- EXTRATO DE SCOUTS (CHUTES NO ALVO ATUALIZADOS) ---")
        contador_exibicao = 0
        for linha in linhas_dados_fin:
            try:
                nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName']")).strip()
                if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                    continue
                
                # Coleta dinâmica de todas as colunas numéricas da linha deste atleta
                colunas = [td.text.strip() for td in linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")]
                print(f"🏃 Atleta: {nome_jogador.ljust(25)} | Estatísticas Carregadas: {colunas}")
                
                contador_exibicao += 1
                if contador_exibicao >= 5: # Limita a exibição de teste no log para os 5 primeiros
                    break
            except:
                continue

    except Exception as e_critico:
        print(f"❌ Falha crítica encontrada no decorrer do teste: {e_critico}")
        
    finally:
        print("\n🏁 Processo de teste concluído. Encerrando driver.")
        driver.quit()
        
