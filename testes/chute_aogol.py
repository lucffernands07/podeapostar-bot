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

# Ajuste para importar módulos da pasta raiz (caso precise futuramente)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")  # Mantido padrão headless moderno
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def testar_captura_chutes():
    # URL inicial de H2H fornecida por você para o teste
    url_h2h_teste = "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/"
    
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    print("\n" + "="*60)
    print("🚀 INICIANDO ANÁLISE DE CHUTES NO ALVO")
    print("="*60 + "\n")
    
    try:
        # ---------------------------------------------------------------------
        # ETAPA 1: Acesso ao H2H Principal
        # ---------------------------------------------------------------------
        driver.get(url_h2h_teste)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        # Coleta nome dos times do topo para o log
        time_a = driver.find_elements(By.CSS_SELECTOR, ".h2h__participant")[0].text.strip()
        time_b = driver.find_elements(By.CSS_SELECTOR, ".h2h__participant")[1].text.strip()
        
        print(f"1. ✅ Acesso ao h2h de {time_a} x {time_b} realizado com sucesso.")
        
        # ---------------------------------------------------------------------
        # ETAPA 2: Encontrar ID do último jogo da Tabela 1 (Sem cliques)
        # ---------------------------------------------------------------------
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        tabela_1 = secoes[0] # Primeira tabela: Últimos jogos do mandante
        
        primeira_linha = tabela_1.find_element(By.CSS_SELECTOR, ".h2h__row")
        
        # Pega os nomes dos times que jogaram essa partida anterior
        time_c = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
        time_d = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
        
        # Extrai o ID único do jogo pelo atributo 'id' do elemento (ex: g_1_lQADNSWu)
        id_bruto = primeira_linha.get_attribute("id")
        id_jogo = id_bruto.replace("g_1_", "").strip()
        
        if not id_jogo:
            raise Exception("Não foi possível isolar o ID do jogo na Tabela 1.")
            
        print(f"2. ✅ Encontrado id do último jogo da tabela 1 ({id_jogo}) -> {time_c} x {time_d}")
        
        # ---------------------------------------------------------------------
        # ETAPA 3: Montagem e Redirecionamento para a URL de Estatísticas
        # ---------------------------------------------------------------------
        url_finalizacoes = f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"3. ✅ URL das estatísticas de finalização gerada: {url_finalizacoes}")
        
        print("\n🔀 Redirecionando navegador para a página alvo...")
        driver.get(url_finalizacoes)
        
        # Tempo de segurança para carregar a página de finalizações
        time.sleep(4)
        
        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: PRONTO PARA A RASPAGEM")
        print("="*60 + "\n")
        
        # Próximo passo: Incluir os scapers das tabelas de finalizações aqui...

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_captura_chutes()
        
