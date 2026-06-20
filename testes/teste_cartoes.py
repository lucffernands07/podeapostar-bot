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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def extrair_cartoes_do_jogo(driver, wait, url_jogo, buscar_casa):
    """
    Navega para a aba GERAIS de estatísticas de jogadores e extrai a soma 
    de cartões (amarelos + vermelhos) do time selecionado (Casa ou Fora).
    """
    try:
        url_limpa = url_jogo.split("?")[0].strip("/")
        
        if "/resumo" in url_limpa:
            url_limpa = url_limpa.split("/resumo")[0]
            
        # Nova URL apontando direto para a aba Geral de estatísticas de jogadores
        url_estatisticas = f"{url_limpa}/resumo/estatisticas-jogadores/gerais/"
        print(f"      🌍 [Navegação] Abrindo estatísticas gerais de jogadores: {url_estatisticas}")
        driver.get(url_estatisticas)
        
        # Aguarda carregar o container que envolve as tabelas de jogadores
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table")))
        
        # O FlashScore geralmente separa em seções/tabelas: seções[0] = Casa, seções[1] = Fora
        tabelas_times = driver.find_elements(By.CSS_SELECTOR, ".ui-table")
        
        if len(tabelas_times) < 2:
            print("      ⚠️ [Aviso] Não foi possível separar as tabelas de jogadores de cada time.")
            return 0
            
        # Define qual tabela analisar baseado no comando (Casa=0, Fora=1)
        tabela_alvo = tabelas_times[0] if buscar_casa else tabelas_times[1]
        
        # Captura todas as linhas de jogadores daquela tabela específica
        linhas_jogadores = tabela_alvo.find_elements(By.CSS_SELECTOR, ".ui-table__row")
        
        total_amarelos = 0
        total_vermelhos = 0
        
        for linha in linhas_jogadores:
            try:
                # No FlashScore, as colunas de dados ficam dentro de divs com classes específicas de células
                celulas = linha.find_elements(By.CSS_SELECTOR, ".ui-table__cell")
                
                # Olhando a estrutura padrão da aba Gerais:
                # As duas últimas colunas são Amarelos e Vermelhos.
                if len(celulas) >= 2:
                    txt_amarelo = celulas[-2].text.strip()
                    txt_vermelho = celulas[-1].text.strip()
                    
                    # Converte se for número (quando não tem cartão, costuma vir um traço '-')
                    total_amarelos += int(txt_amarelo) if txt_amarelo.isdigit() else 0
                    total_vermelhos += int(txt_vermelho) if txt_vermelho.isdigit() else 0
            except Exception as e:
                continue
                
        total_cartoes_time = total_amarelos + total_vermelhos
        tipo_time = "Casa" if buscar_casa else "Visitante"
        print(f"      ✅ [Resultado {tipo_time}] Amarelos: {total_amarelos} | Vermelhos: {total_vermelhos} | Total: {total_cartoes_time}")
        
        return total_cartoes_time

    except Exception as e:
        print(f"      ❌ [Erro] Falha ao ler a tabela de jogadores: {e}")
    return 0
    
def testar_analise_cartoes():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/brasil-I9l9aqLq/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 [TESTE INDESTRUTÍVEL] ANÁLISE DE CARTÕES VIA ABAS GERAIS")
    print("="*60 + "\n")
    
    historico_mandante = []
    historico_visitante = []
    
    try:
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        # --- TABELA 1: MANDANTE ---
        print("📦 Coletando dados da TABELA 1 (Últimos jogos do Mandante)...")
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t1 = secoes[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_mandante = []
        for linha in linhas_t1:
            try:
                link_el = linha.find_element(By.TAG_NAME, "a") if linha.find_elements(By.TAG_NAME, "a") else linha
                href = link_el.get_attribute("href") or link_el.get_attribute("data-url")
                if href:
                    urls_mandante.append(href)
            except:
                continue

        if not urls_mandante:
            for linha in linhas_t1:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_mandante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}")

        for idx, url in enumerate(urls_mandante[:3]):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=True)
            historico_mandante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões acumulados pelo time")

        # --- TABELA 2: VISITANTE ---
        print("\n📦 Coletando dados da TABELA 2 (Últimos jogos do Visitante)...")
        driver.get(url_inicial)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        linhas_t2 = secoes[1].find_elements(By.CSS_SELECTOR, ".h2h__row")[:3]
        
        urls_visitante = []
        for linha in linhas_t2:
            try:
                link_el = inline_el = linha.find_element(By.TAG_NAME, "a") if linha.find_elements(By.TAG_NAME, "a") else linha
                href = link_el.get_attribute("href") or link_el.get_attribute("data-url")
                if href:
                    urls_visitante.append(href)
            except:
                continue

        if not urls_visitante:
            for linha in linhas_t2:
                id_attr = linha.get_attribute("id") or ""
                if "_" in id_attr:
                    id_jogo = id_attr.split('_')[-1]
                    urls_visitante.append(f"https://www.flashscore.com.br/jogo/{id_jogo}")

        for idx, url in enumerate(urls_visitante[:3]):
            cartoes = extrair_cartoes_do_jogo(driver, wait, url, buscar_casa=False)
            historico_visitante.append(cartoes)
            print(f"  ➔ Jogo {idx+1}: {cartoes} cartões acumulados pelo time")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        print("\n" + "="*60)
        print("📊 RESULTADO DO CONFRONTO (SOMA DAS ABAS GERAIS)")
        print("="*60)
        print(f"🟨 Lista Mandante: {historico_mandante}")
        print(f"🟨 Lista Visitante: {historico_visitante}")
        
        total_cartoes = sum(historico_mandante) + sum(historico_visitante)
        media_6_jogos = total_cartoes / 6
        
        print(f"\n📊 Média de cartões (6 jogos combinados): {media_6_jogos:.2f}")
        
        if media_6_jogos < 2.5:
            print("   💡 Tendência: -2.5 cartões")
        else:
            print("   💡 Tendência: +2.5 cartões")

    except Exception as e:
        print(f"\n❌ Erro no fluxo de execução: {e}")
    finally:
        driver.quit()
        print("\n🏁 Processo finalizado.")

if __name__ == "__main__":
    testar_analise_cartoes()
