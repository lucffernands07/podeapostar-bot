import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def testar_navegação_direta_home(time_casa, time_fora):
    options = Options()
    # options.add_argument("--headless") # Descomente para rodar escondido
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print(f"\n🚀 --- INICIANDO TESTE NA HOME: {time_casa} x {time_fora} ---")
    
    try:
        # 1. ACESSA A HOME
        driver.get("https://www.sofascore.com/pt/")
        print("✅ LOG: Home do SofaScore carregada.")
        time.sleep(5) # Espera o carregamento dos jogos do dia

        # 2. BUSCA O JOGO NA LISTA DA HOME
        # Procura por um elemento que contenha o nome de um dos times
        print(f"🔍 LOG: Procurando o jogo {time_casa} na lista de hoje...")
        try:
            # Seletor que busca o texto do time dentro da lista de eventos
            seletor_jogo = f"//div[contains(text(), '{time_casa}')]"
            jogo_elemento = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, seletor_jogo))
            )
            # Sobe para o elemento 'a' pai que contém o link do jogo
            link_jogo = jogo_elemento.find_element(By.XPATH, "./ancestor::a")
            driver.execute_script("arguments[0].scrollIntoView(true);", link_jogo)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", link_jogo)
            print(f"✅ LOG: Jogo encontrado e clicado!")
        except Exception as e:
            print(f"❌ LOG ERRO: Jogo não encontrado na lista da Home. (O jogo é hoje?)")
            return

        # 3. CLICA NA ABA PARTIDAS (H2H)
        print("⏳ LOG: Aguardando carregamento da página do jogo...")
        try:
            # Usando o seletor exato que você passou
            aba_partidas = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#tab:matches"]'))
            )
            driver.execute_script("arguments[0].click();", aba_partidas)
            print("✅ LOG: Aba 'Partidas' (H2H) aberta!")
            time.sleep(8) # Tempo para carregar os cards de estatísticas
        except Exception as e:
            print(f"❌ LOG ERRO: Não encontrou o botão 'Partidas': {e}")
            return

        # 4. RASPAGEM DOS VALORES
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        # Expressão regular para capturar os blocos de 10.5 escanteios
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
                print(f"   🔹 Posição {i}: {num}/{den} ({perc:.1f}%)")

        # 5. VALIDAÇÃO DA 7ª E 8ª POSIÇÃO
        if len(frequencias) >= 8:
            casa_val = frequencias[6] # 7ª posição
            fora_val = frequencias[7] # 8ª posição
            print(f"\n🏠 LOG CASA (7ª): {casa_val:.1f}%")
            print(f"🚌 LOG VISITANTE (8ª): {fora_val:.1f}%")
            print(f"📈 MÉDIA FINAL: {(casa_val + fora_val)/2:.1f}%")
        else:
            print(f"\n⚠️ LOG AVISO: Apenas {len(frequencias)} frações encontradas. Precisamos de pelo menos 8.")

    except Exception as e:
        print(f"🚨 LOG ERRO CRÍTICO: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    # Teste com Como x Roma (Certifique-se que o jogo aparece na home hoje)
    testar_navegação_direta_home("Como", "Roma")
            
