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
        
        time_a = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__home .participant__participantName").text.strip()
        time_b = driver.find_element(By.CSS_SELECTOR, ".duelParticipant__away .participant__participantName").text.strip()
        
        print(f"1. ✅ Acesso ao h2h de {time_a} x {time_b} realizado com sucesso.")
        
        # ---------------------------------------------------------------------
        # ETAPA 2: Simular clique na primeira linha para pegar o ID pela URL
        # ---------------------------------------------------------------------
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        tabela_1 = secoes[0] 
        
        # Localiza a primeira linha do confronto
        primeira_linha = tabela_1.find_element(By.CSS_SELECTOR, ".h2h__row")
        
        time_c = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
        time_d = primeira_linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
        
        print(f"🔄 Elemento de {time_c} x {time_d} localizado. Disparando clique simulado...")
        
        # Executa o clique via JavaScript diretamente no elemento da linha para evitar bloqueio de overlay
        driver.execute_script("arguments[0].click();", primeira_linha)
        
        # Espera curta para garantir a mudança de página
        time.sleep(4)
        
        # Pega a URL atual do navegador (Ex: https://www.flashscore.com.br/jogo/lQADNSWu/#/resumo)
        url_remanecente = driver.current_url
        
        # Corta a URL para extrair o ID do jogo
        partes_url = url_remanecente.strip("/").split("#")[0].split("/")
        id_jogo = partes_url[-1] if partes_url[-1] != "resumo" else partes_url[-2]
        
        # Se por acaso o ID contiver traços (nome do time junto), pega a última parte dele
        if "-" in id_jogo:
            id_jogo = id_jogo.split("-")[-1]
            
        print(f"2. ✅ Navegação detectada. ID extraído da URL atual ({id_jogo}) -> {time_c} x {time_d}")
        
        # ---------------------------------------------------------------------
        # ETAPA 3: Redirecionamento para a Página Alvo de Finalizações
        # ---------------------------------------------------------------------
        url_finalizacoes_direta = f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"3. ✅ URL das estatísticas de finalização gerada: {url_finalizacoes_direta}")
        
        print("\n🔀 Redirecionando navegador para a página alvo...")
        driver.get(url_finalizacoes_direta)
        
        time.sleep(6)
        
        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: PRONTO PARA A RASPAGEM")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_captura_chutes()
    
