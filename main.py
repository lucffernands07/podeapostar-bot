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

def configurar_browser():
    options = Options()
    # CONFIGURAÇÕES OBRIGATÓRIAS PARA GITHUB ACTIONS (SERVER-SIDE)
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # User-agent para evitar ser bloqueado como bot básico
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_navegação_direta_home(time_casa, time_fora):
    driver = configurar_browser()
    
    print(f"\n🚀 --- INICIANDO DIAGNÓSTICO: {time_casa} x {time_fora} ---")
    
    try:
        # 1. ACESSA A HOME
        print("🌐 LOG: Acessando https://www.sofascore.com/pt/ ...")
        driver.get("https://www.sofascore.com/pt/")
        time.sleep(7) # Espera carregar a lista de jogos

        # 2. BUSCA O JOGO NA LISTA
        print(f"🔍 LOG: Buscando o time '{time_casa}' na lista de jogos de hoje...")
        try:
            # Busca pelo texto do time
            xpath_jogo = f"//div[contains(text(), '{time_casa}')]"
            elemento_time = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath_jogo))
            )
            
            # Sobe para o link do evento
            link_evento = elemento_time.find_element(By.XPATH, "./ancestor::a")
            url_jogo = link_evento.get_attribute("href")
            print(f"✅ LOG: Jogo encontrado! URL: {url_jogo}")
            
            # Navega para o jogo
            driver.get(url_jogo)
        except Exception as e:
            print(f"❌ LOG ERRO: Não encontrou o jogo '{time_casa}' na home. Verifique se ele joga hoje.")
            return

        # 3. ABRE A ABA PARTIDAS (H2H)
        print("⏳ LOG: Abrindo aba 'Partidas' para H2H...")
        try:
            # Força a URL da aba se o clique falhar
            url_h2h = driver.current_url + "#tab:matches"
            driver.get(url_h2h)
            time.sleep(10) # Tempo vital para o JavaScript carregar as frações 0/0
            print("✅ LOG: Aba Partidas carregada via URL direta.")
        except Exception as e:
            print(f"❌ LOG ERRO ao acessar aba Partidas: {e}")
            return

        # 4. RASPAGEM DOS VALORES (REGRA 7ª E 8ª FRAÇÃO)
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # Encontra todas as ocorrências de "10.5 escanteios"
        matches = list(re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE))
        print(f"\n📊 LOG: Encontrados {len(matches)} blocos de 10.5 escanteios.")

        frequencias = []
        for i, m in enumerate(matches, 1):
            trecho = texto_bruto[m.end() : m.end() + 60]
            frequencia = re.search(r"(\d+)/(\d+)", trecho)
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)
                print(f"   📍 Posição {i}: {num}/{den} ({perc:.1f}%)")

        # 5. VALIDAÇÃO FINAL
        print("\n--- RESULTADO DA ANÁLISE ---")
        if len(frequencias) >= 8:
            casa_perc = frequencias[6] # 7ª posição (índice 6)
            fora_perc = frequencias[7] # 8ª posição (índice 7)
            print(f"🏠 CASA (7ª): {casa_perc:.1f}%")
            print(f"🚌 VISITANTE (8ª): {fora_perc:.1f}%")
            print(f"📈 MÉDIA H2H: {(casa_perc + fora_perc)/2:.1f}%")
        else:
            print(f"⚠️ AVISO: Apenas {len(frequencias)} frações encontradas. O SofaScore pode não ter os dados de H2H completos para este jogo.")

    except Exception as e:
        print(f"🚨 LOG ERRO CRÍTICO: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    # Certifique-se que o time escrito aqui é EXATAMENTE como aparece no SofaScore
    testar_navegação_direta_home("Como", "Roma")
            
