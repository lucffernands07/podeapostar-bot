import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def extrair_cartoes_do_jogo(driver, url_jogo, buscar_casa):
    """
    Abre o jogo em uma nova aba, acessa a aba de estatísticas,
    extrai os cartões e printa os logs detalhados do DOM.
    """
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    val_cartoes = 0
    try:
        # Garante o link direto para as estatísticas do resumo
        url_resumo = driver.current_url.split("?")[0].strip("/") + "/resumo/estatisticas/"
        driver.get(url_resumo)
        time.sleep(3.0) # Tempo seguro para o carregamento do DOM dinâmico
        
        # Encontra as linhas de estatísticas pelo seletor correto do DevTools
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics']")
        
        cartoes_achados = False
        for linha in linhas:
            try:
                cat_el = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-statistics-category']")
                texto_categoria = cat_el.text.upper().strip()
                
                if "CARTÕES AMARELOS" in texto_categoria or "CARTÃO AMARELO" in texto_categoria:
                    valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-statistics-value']")
                    
                    if len(valores) >= 2:
                        txt_casa = valores[0].text.strip()
                        txt_fora = valores[1].text.strip()
                        
                        val_casa = int(txt_casa) if txt_casa.isdigit() else 0
                        val_fora = int(txt_fora) if txt_fora.isdigit() else 0
                        
                        val_cartoes = val_casa if buscar_casa else val_fora
                        print(f"      🟨 [Cartões do Jogo] Casa: {val_casa} | Visitante: {val_fora} -> (Alvo extraído: {val_cartoes})")
                        cartoes_achados = True
                        break
            except:
                continue
                
        if not cartoes_achados:
            print("      ⚠️ [Aviso] Estatística de 'Cartões Amarelos' não disponível ou zerada para este jogo.")
            
    except Exception as e:
        print(f"      ❌ [Erro] Falha ao raspar estatísticas da partida: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
    return val_cartoes
    
def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE INDESTRUTÍVEL] ANÁLISE DE CARTÕES COMPLETA")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        print(f"🌍 [Navegação] Acessando URL Base: {url_inicial}")
        driver.get(url_inicial)
        
        # Espera flexível aceitando a classe antiga ou o data-testid novo do H2H
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row, [data-testid='wcl-h2h-row']")))
        except Exception as e:
            print("❌ [Erro Crítico] Elementos H2H não carregaram na página principal!")
            # Print do HTML para debug se falhar
            print(f"DOM atual do container principal: {driver.find_element(By.TAG_NAME, 'body').text[:500]}")
            return

        # Captura as seções (Tabela 1: Mandante, Tabela 2: Visitante)
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [data-testid='wcl-h2h-section']")
        print(f"🔍 [DOM] Foram encontradas {len(secoes)} seções de H2H na página.")
        
        if len(secoes) < 2:
            print("⚠️ [Aviso] Menos de 2 seções encontradas. Tentando buscar linhas globais...")
            
        # --- TABELA 1: MANDANTE ---
        print("\n📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row, [data-testid='wcl-h2h-row']")[:3]
        print(f"🔍 [DOM] Encontradas {len(linhas_t1)} linhas de jogos na Tabela do Mandante.")
        
        urls_mandante = []
        for idx, linha in enumerate(linhas_t1):
            try:
                id_attr = linha.get_attribute("id") or ""
                # Se não tiver id, tenta pegar o atributo data-id ou herdar do click
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    url_completa = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
                    urls_mandante.append(url_completa)
                    print(f"   ➔ Identificado Jogo {idx+1} (Mandante) -> ID: {id_jogo} | URL: {url_completa}")
            except Exception as e:
                print(f"   ⚠️ Erro ao processar linha {idx+1} do Mandante: {e}")
                continue

        # Executa a raspagem nas URLs coletadas do Mandante
        for idx, url in enumerate(urls_mandante):
            print(f"   🌍 [Navegação] Processando partida {idx+1}/3 do Mandante...")
            cartoes = extrair_cartoes_do_jogo(driver, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"   ➔ Resultado Salvo para Mandante no Jogo {idx+1}: {cartoes} cartões\n")

        # --- TABELA 2: VISITANTE ---
        print("📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row, [data-testid='wcl-h2h-row']")[:3]
        print(f"🔍 [DOM] Encontradas {len(linhas_t2)} linhas de jogos na Tabela do Visitante.")
        
        urls_visitante = []
        for idx, linha in enumerate(linhas_t2):
            try:
                id_attr = grandfather_id = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    url_completa = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
                    urls_visitante.append(url_completa)
                    print(f"   ➔ Identificado Jogo {idx+1} (Visitante) -> ID: {id_jogo} | URL: {url_completa}")
            except Exception as e:
                print(f"   ⚠️ Erro ao processar linha {idx+1} do Visitante: {e}")
                continue

        # Executa a raspagem nas URLs coletadas do Visitante
        for idx, url in enumerate(urls_visitante):
            print(f"   🌍 [Navegação] Processando partida {idx+1}/3 do Visitante...")
            cartoes = extrair_cartoes_do_jogo(driver, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"   ➔ Resultado Salvo para Visitante no Jogo {idx+1}: {cartoes} cartões\n")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        print("="*60)
        print("📊 RESULTADO DO CONFRONTO")
        print("="*60)
        print(f"🟨 Lista Mandante: {historico_mandante}")
        print(f"🟨 Lista Visitante: {historico_visitante}")

    except Exception as e:
        print(f"\n❌ Erro no fluxo geral de execução: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
