import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO DO BROWSER (MANTIDA IGUAL AO SEU) ---
def configurar_browser():
    options = Options()
    options.add_argument("--headless=new") # Rode em headless para simular o GitHub Actions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def executar_teste_individual():
    # LINK ALVO FORNECIDO
    url_confronto = "https://www.sofascore.com/pt/football/match/red-bull-bragantino-bahia/fOsZO"
    
    print(f"\n🚀 === INICIANDO TESTE DE RASPAGEM INDIVIDUAL === 🚀")
    print(f"🌍 Jogo Alvo: Bragantino x Bahia")
    print(f"🔗 URL: {url_confronto}\n")
    
    driver = configurar_browser()
    wait = WebDriverWait(driver, 30) # Wait alto para garantir carregamento
    
    try:
        # LOG PROCESSO 1
        print(f"[LOG 1] Acessando a página do confronto...")
        driver.get(url_confronto)
        time.sleep(10) # Tempo para renderizar os elementos dinâmicos

        # Tentar fechar cookies se aparecer (boa prática)
        try:
            cookies = driver.find_elements(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Agree')]")
            if cookies: 
                cookies[0].click()
                print("[LOG] Cookies aceitos.")
        except: pass

        # --- FUNÇÃO INTERNA DE RASPAGEM POR TIME ---
        def raspar_dados_time(xpath_clique_time, nome_time_log):
            try:
                # LOG PROCESSO 2/5
                print(f"[LOG] Clicando no time: {nome_time_log}...")
                
                # SELETOR PRECISO: Baseado no <bdi> que você forneceu, mas buscando pelo texto contido
                seletor_time = f"//bdi[contains(text(), '{nome_time_log}')]"
                btn_time = wait.until(EC.element_to_be_clickable((By.XPATH, seletor_time)))
                
                # Rolar até o elemento antes de clicar (evita erros de clique interceptado)
                driver.execute_script("arguments[0].scrollIntoView(true);", btn_time)
                time.sleep(2)
                btn_time.click()
                print(f"[LOG] Página do {nome_time_log} carregada.")
                time.sleep(8)

                # LOG PROCESSO 3/6
                print(f"[LOG] Clicando na aba 'Estatísticas' do {nome_time_log}...")
                
                # SELETOR PRECISO: Baseado na tag <a> com href='#tab:statistics' que você forneceu
                seletor_aba = "//a[@href='#tab:statistics']"
                btn_aba = wait.until(EC.element_to_be_clickable((By.XPATH, seletor_aba)))
                btn_aba.click()
                print(f"[LOG] Aba Estatísticas do {nome_time_log} aberta.")
                time.sleep(6)

                # Rolar para baixo para carregar o grid de stats
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(3)

                # LOG PROCESSO 4/7
                print(f"[LOG] Buscando 'Total de finalizações por jogo' do {nome_time_log}...")
                
                # Raspagem por texto bruto (como na função de cantos original)
                texto_pagina = driver.find_element(By.TAG_NAME, "body").text
                
                # REGEX ESPECÍFICO: Procura a frase exata e captura o número (ex: 12.4)
                match = re.search(r"Total de finalizações por jogo\s*(\d+[\.,]\d+)", texto_pagina, re.IGNORECASE)
                
                if match:
                    valor = float(match.group(1).replace(',', '.'))
                    print(f"✅ [SUCESSO] Média {nome_time_log}: {valor}")
                    
                    # Volta para a página do jogo para pegar o próximo time
                    print(f"[LOG] Voltando para a página do confronto...")
                    driver.back() # Volta das Estatísticas para o perfil
                    time.sleep(3)
                    driver.back() # Volta do perfil para o Jogo
                    time.sleep(5)
                    return valor
                else:
                    print(f"❌ [FALHA] Não encontrou o texto 'Total de finalizações por jogo' na página do {nome_time_log}.")
                    # Tenta voltar de qualquer forma
                    driver.get(url_confronto)
                    time.sleep(8)
                    return 0
            except Exception as e:
                print(f"❌ [ERRO] Falha crítica na raspagem do {nome_time_log}: {e}")
                # Tenta voltar para a URL base para não quebrar o próximo
                driver.get(url_confronto)
                time.sleep(8)
                return 0

        # --- EXECUÇÃO DOS DOIS TIMES (BAHIA x BRAGANTINO) ---
        # Note que o link fornecido é Red Bull Bragantino x Bahia, 
        # mas os elementos que você passou foram Bahia (Casa) e Adversário (Fora).
        # Vou seguir a ordem de quem está à esquerda na tela (Casa).
        
        # Pega as médias
        media_casa = raspar_dados_time("//bdi[contains(text(), 'Bahia')]", "Bahia")
        media_fora = raspar_dados_time("//bdi[contains(text(), 'Red Bull Bragantino')]", "Red Bull Bragantino")

        # --- CÁLCULO FINAL ---
        print(f"\n📊 === RESULTADO FINAL DO TESTE === 📊")
        if media_casa > 0 and media_fora > 0:
            soma = media_casa + media_fora
            media_final = soma / 2
            print(f"🏠 Média Bahia: {media_casa:.2f}")
            print(f"🚌 Média Bragantino: {media_fora:.2f}")
            print(f"🧮 Soma: {soma:.2f} | Divisor: 2")
            print(f"🎯 Média Final: {media_final:.2f}")
            
            # Validação da Regra > 10.5
            if media_final > 10.5:
                print(f"✅ [APROVADO] Média {media_final:.2f} é MAIOR que 10.5. Mercado Escanteio entra.")
            else:
                print(f"⚠️ [REJEITADO] Média {media_final:.2f} é MENOR ou IGUAL a 10.5. Mercado Escanteio fora.")
        else:
            print(f"❌ [FALHA GERAL] Não foi possível obter as médias de ambos os times para o cálculo.")

    except Exception as e:
        print(f"❌ [ERRO MESTRE] Ocorreu um erro inesperado no script: {e}")
        
    finally:
        print(f"\n🛑 Encerrando o browser...")
        driver.quit()
        print(f"=== TESTE FINALIZADO ===\n")

if __name__ == "__main__":
    executar_teste_individual()
    
