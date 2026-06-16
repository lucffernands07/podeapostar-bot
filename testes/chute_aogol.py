import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def testar_captura_chutes():
    # Configuração do WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Ativar apenas em produção
    options.add_argument('--start-maximized')
    options.add_argument('--log-level=3') # Limpa avisos bobos do Chrome no terminal
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    # URL do H2H inicial (França x Senegal)
    url_h2h_teste = "https://www.flashscore.com.br/jogo/futebol/franca-QkGeVG1n/senegal-hOIsJLJr/h2h/total/"
    
    print("\n" + "="*60)
    print("🚀 INICIANDO ANÁLISE DE CHUTES NO ALVO")
    print("="*60 + "\n")
    
    try:
        # ---------------------------------------------------------------------
        # ETAPA 1: Acesso ao H2H Principal
        # ---------------------------------------------------------------------
        driver.get(url_h2h_teste)
        # Aguarda a estrutura do H2H carregar na página
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "h2h__section")))
        
        # Captura os nomes dos times principais direto no topo para o log
        # Geralmente no H2H os nomes ficam nos headers das tabelas ou no placar
        time_a = driver.find_elements(By.CLASS_NAME, "h2h__participant")[0].text.strip()
        time_b = driver.find_elements(By.CLASS_NAME, "h2h__participant")[1].text.strip()
        
        print(f"1. ✅ Acesso ao h2h de {time_a} x {time_b} realizado com sucesso.")
        
        # ---------------------------------------------------------------------
        # ETAPA 2: Encontrar ID e nomes do último jogo da Tabela 1
        # ---------------------------------------------------------------------
        # Isola a primeira tabela (Últimos jogos do mandante)
        tabela_1 = driver.find_elements(By.CLASS_NAME, "h2h__section")[0]
        
        # Pega a linha do jogo mais recente (primeira linha do bloco)
        primeira_linha = tabela_1.find_element(By.CLASS_NAME, "h2h__row")
        
        # Extrai os nomes dos times envolvidos nessa partida do passado
        time_c = primeira_linha.find_element(By.CLASS_NAME, "h2h__homeParticipant").text.strip()
        time_d = primeira_linha.find_element(By.CLASS_NAME, "h2h__awayParticipant").text.strip()
        
        # Extrai o ID único do jogo pelo atributo do DOM (ex: g_1_lQADNSWu)
        id_bruto = primeira_linha.get_attribute("id")
        id_jogo = id_bruto.replace("g_1_", "").strip()
        
        if not id_jogo:
            raise Exception("Falha ao isolar o ID do jogo na tabela 1.")
            
        print(f"2. ✅ Encontrado id do último jogo da tabela 1 ({id_jogo}) -> {time_c} x {time_d}")
        
        # ---------------------------------------------------------------------
        # ETAPA 3: Montagem e Acesso à URL de Estatísticas de Finalização
        # ---------------------------------------------------------------------
        url_finalizacoes = f"https://www.flashscore.com.br/jogo/{id_jogo}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"3. ✅ URL das estatísticas de finalização gerada: {url_finalizacoes}")
        
        # Redireciona o navegador direto para a página final de estatísticas
        print("\n🔀 Redirecionando navegador para a página alvo...")
        driver.get(url_finalizacoes)
        
        # Dá um pequeno tempo para a página assentar visualmente (bom para debug)
        time.sleep(3)
        
        print("\n" + "="*60)
        print("🎉 FIM DA ETAPA DE OTIMIZAÇÃO: PRONTO PARA A RASPAGEM")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A EXECUÇÃO: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    testar_captura_chutes()
