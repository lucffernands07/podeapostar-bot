import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Ajuste para importar módulos da pasta raiz
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

def testar_captura_chutes():
    # URL inicial do H2H de França x Senegal
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
        
        # Pega os nomes do topo do confronto principal
        time_a = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home .participant__participantName").text.strip()
        time_b = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away .participant__participantName").text.strip()
        
        print(f"1. ✅ Acesso ao h2h de {time_a} x {time_b} realizado com sucesso.")
        
        # ---------------------------------------------------------------------
        # ETAPA 2: Encontrar ID do último jogo da Tabela 1 (Via tag <a>)
        # ---------------------------------------------------------------------
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        tabela_1 = secoes[0] # Isola a primeira tabela (Últimos jogos de França)
        
        # Seleciona a primeira linha de confronto
        primeira_linha = tabela_1.find_element(By.CSS_SELECTOR, ".h2h__row")
        
        time_c = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
        time_d = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
        
        # Nova estratégia: Buscar o link interativo ('a') que envelopa a linha ou o resultado
        elemento_link = primeira_linha.find_element(By.CSS_SELECTOR, "a")
        url_jogo_anterior = elemento_link.get_attribute("href")
        
        if not url_jogo_anterior:
            raise Exception("Não foi possível encontrar o atributo 'href' na primeira linha do H2H.")
            
        # Exemplo de URL: https://www.flashscore.com.br/jogo/lQADNSWu/
        # Removemos barras extras nas pontas e quebramos por '/' para isolar o ID no final
        partes_url = url_jogo_anterior.strip("/").split("/")
        id_jogo = partes_url[-1]
        
        if not id_jogo or len(id_jogo) < 5:
            raise Exception(f"ID extraído da URL parece inválido: '{id_jogo}'")
            
        print(f"2. ✅ Encontrado id do último jogo da tabela 1 ({id_jogo}) -> {time_c} x {time_d}")
        
        # ---------------------------------------------------------------------
        # ETAPA 3: Montagem e Redirecionamento para a Página de Finalizações
        # ---------------------------------------------------------------------
        # Montagem sem o caractere hash (#), direto para a rota estática limpa
        url_finalizacoes_direta = f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
        
        print(f"3. ✅ URL das estatísticas de finalização gerada: {url_finalizacoes_direta}")
        
        print("\n🔀 Redirecionando navegador para a página alvo...")
        driver.get(url_finalizacoes_direta)
        
        # Tempo de segurança para o carregamento do DOM dinâmico com a lista de jogadores (Ex: Mbappe K.)
        time.sleep(6)
        
        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: PRONTO PARA A RASPAGEM")
        print("="*60 + "\n")
        
        # O robô agora parou exatamente na página do segundo print, pronto para ler a tabela.
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_captura_chutes()
    
