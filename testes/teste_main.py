import os
import time
import re
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
    URL_H2H_ALVO = "https://www.flashscore.com.br/jogo/futebol/noruega-8rP6JO0H/senegal-hOIsJLJr/h2h/total/"
    
    print("🚀 Inicializando driver com as configurações do main.py...")
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)

    # Índice simulando o jogo atual dentro do loop (0 para o primeiro jogo)
    jogo_global_index = 0

    stats = {
        "historico_chutes": {},
        "historico_mandante_am": {}, "historico_mandante_vm": {}
    }

    try:
        print(f"🔋 [RASPAGEM 1] Acessando aba H2H: {URL_H2H_ALVO}")
        driver.get(URL_H2H_ALVO)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row")
        print(f"✅ Sucesso! Encontrados {len(linhas_confrontos)} confrontos históricos no painel.")

        if len(linhas_confrontos) == 0:
            driver.quit()
            exit()

        elemento_jogo = linhas_confrontos[0]
        texto_jogo = elemento_jogo.text.replace('\n', ' ')
        print(f"🏟️ Abrindo jogo histórico: {texto_jogo}")

        driver.execute_script("arguments[0].click();", elemento_jogo)
        time.sleep(3)

        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        url_jogo_completa = driver.current_url.split("?")[0].split("#")[0].strip("/")
        print(f"🔗 URL Base do Jogo de Scout Detectada: {url_jogo_completa}")

        # -----------------------------------------------------------------
        # 🗂️ PASSO 1: RASPAGEM DE CARTÕES (ABA GERAIS)
        # -----------------------------------------------------------------
        url_gerais = f"{url_jogo_completa}/resumo/estatisticas-jogadores/gerais/"
        print(f"\n🃏 [RASPAGEM 2.1] Entrando na Aba Gerais (Cartões): {url_gerais}")
        driver.get(url_gerais)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
        time.sleep(1.5)
        
        texto_trava_antigo = ""
        try:
            celula_dados = driver.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
            texto_trava_antigo = driver.execute_script("return arguments[0].textContent;", celula_dados).strip()
            print(f"🔒 Valor de controle registrado na Aba Cartões: '{texto_trava_antigo}'")
        except:
            pass

        # -----------------------------------------------------------------
        # 🎯 PASSO 2: RASPAGEM DE CHUTES NO ALVO (ABA FINALIZAÇÕES)
        # -----------------------------------------------------------------
        url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"\n🎯 [RASPAGEM 2.2] Modificando para Aba Finalizações: {url_finalizacoes}")
        driver.get(url_finalizacoes)
        
        print("🛡️ [BLINDAGEM] Sincronizando transição de estado da tabela...")
        
        if texto_trava_antigo:
            try:
                wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != texto_trava_antigo)
                print("🔄 [SINCRO] Sucesso! O navegador identificou a mudança de dados da sub-aba.")
            except:
                print("⚠️ Aviso: Tempo limite da trava atingido. Prosseguindo.")
        else:
            wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']").text.strip() != "")

        time.sleep(1.2)

        # 🔍 DESCOBRE DINAMICAMENTE O ÍNDICE DA COLUNA DE CHUTES NO ALVO
        cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
        indice_chutes = -1
        
        for idx_th, th in enumerate(cabecalhos_fin):
            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
            alias = str(th.get_attribute("data-analytics-alias")).upper()
            
            if "CHUTE" in texto_th or "ALVO" in texto_th or alias == "SHOTS_ON_TARGET" or texto_th == "FN":
                indice_chutes = idx_th
                print(f"🎯 Coluna de Chutes no Alvo mapeada dinamicamente no Índice: {indice_chutes} ('{texto_th}')")
                break

        # Fallback se o mapeamento falhar
        if indice_chutes == -1:
            indice_chutes = 5
            print(f"⚠️ Não foi possível mapear o cabeçalho. Usando Fallback padrão no índice {indice_chutes}")

        linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
        print(f"📊 Total de linhas identificadas na tabela final: {len(linhas_dados_fin)}")
        
        print("\n📝 --- GRAVAÇÃO DOS DADOS FILTRADOS NO DICIONÁRIO ---")
        for linha in linhas_dados_fin:
            try:
                nome_bruto = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName']")).strip()
                if not nome_bruto or nome_bruto == "TODOS" or "JOGADOR" in nome_bruto.upper():
                    continue
                
                # 🧼 Limpa a quebra de linha para separar o nome da posição do jogador
                nome_jogador = nome_bruto.split('\n')[0].strip()
                
                celulas_valores = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                if not celulas_valores or len(celulas_valores) <= indice_chutes:
                    continue

                val_chute = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes]).strip()
                
                # Transforma hífens ou vazios em 0
                chutes_no_alvo = 0 if val_chute in ["-", ""] or not val_chute.isdigit() else int(val_chute)

                # Aloca no dicionário simulado
                if nome_jogador not in stats["historico_chutes"]:
                    stats["historico_chutes"][nome_jogador] = []
                
                while len(stats["historico_chutes"][nome_jogador]) < jogo_global_index:
                    stats["historico_chutes"][nome_jogador].append(0)
                    
                stats["historico_chutes"][nome_jogador].append(chutes_no_alvo)

                # Destaca no log do GitHub se capturar o Haaland com o valor limpo
                if "HAALAND" in nome_jogador.upper():
                    print(f"🔥 [GRAVADO] Atleta: {nome_jogador.ljust(15)} | Chutes no Alvo: {stats['historico_chutes'][nome_jogador]}")

            except:
                continue

    except Exception as e_critico:
        print(f"❌ Falha crítica no teste: {e_critico}")
        
    finally:
        print("\n🏁 Processo de teste concluído. Encerrando driver.")
        driver.quit()
