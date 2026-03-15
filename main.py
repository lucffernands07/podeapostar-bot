import urllib.parse
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def testar_analise_detalhada(t1, t2):
    options = Options()
    options.add_argument("--headless") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print(f"\n🔍 --- INICIANDO DIAGNÓSTICO: {t1} x {t2} ---")
    
    try:
        # 1. BUSCA NO GOOGLE
        query = urllib.parse.quote(f"sofascore {t1} {t2} match")
        driver.get(f"https://www.google.com/search?q={query}")
        
        link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
        print(f"✅ LOG: Partida encontrada no Google. Entrando no SofaScore...")
        link.click()

        # 2. ESPERA REDIRECIONAMENTO
        WebDriverWait(driver, 15).until(EC.url_contains("sofascore.com"))
        print(f"✅ LOG: SofaScore carregado. URL: {driver.current_url}")

        # 3. ABA PARTIDAS
        print(f"⏳ LOG: Tentando abrir a aba 'Partidas'...")
        try:
            # Tenta clicar pelo texto ou pelo href
            aba = WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(., 'Partidas') or contains(@href, 'matches')]"))
            )
            driver.execute_script("arguments[0].click();", aba)
            time.sleep(8) # Tempo crucial para carregar os cards de estatísticas
            print(f"✅ LOG: Aba 'Partidas' aberta com sucesso!")
        except Exception as e:
            print(f"❌ LOG ERRO: Não conseguiu abrir a aba 'Partidas'. Verifique o seletor.")

        # 4. EXTRAÇÃO E MAPEAMENTO DE FRAÇÕES
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        print(f"\n📊 --- MAPEAMENTO DE ESTATÍSTICAS (10.5 ESCANTEIOS) ---")
        
        matches = list(re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE))
        print(f"Encontrados {len(matches)} blocos de '10.5 escanteios' no texto bruto.")

        frequencias_encontradas = []
        
        for i, m in enumerate(matches, 1):
            # Pega um trecho maior após o texto para garantir que a fração esteja dentro
            trecho = texto_bruto[m.end() : m.end() + 60]
            frequencia = re.search(r"(\d+)/(\d+)", trecho)
            
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias_encontradas.append(perc)
                print(f"📍 Fração na posição {i}: {num}/{den} ({perc:.1f}%)")
            else:
                print(f"📍 Fração na posição {i}: Não encontrada no trecho: '{trecho[:20]}...'")

        # 5. VALIDAÇÃO DA REGRA (7ª e 8ª)
        print(f"\n🎯 --- VALIDAÇÃO DA REGRA (7ª e 8ª) ---")
        
        if len(frequencias_encontradas) >= 8:
            casa = frequencias_encontradas[6]  # Índice 6 é a 7ª posição
            fora = frequencias_encontradas[7]  # Índice 7 é a 8ª posição
            
            print(f"🏠 LOG CASA (7ª): {casa:.1f}%")
            print(f"🚌 LOG VISITANTE (8ª): {fora:.1f}%")
            
            media = (casa + fora) / 2
            print(f"📈 MÉDIA FINAL H2H: {media:.1f}%")
            
            if media >= 85:
                print("✅ RESULTADO: Jogo aprovado para o bilhete!")
            else:
                print("⚠️ RESULTADO: Média abaixo de 85%.")
        else:
            print(f"❌ LOG FALHA: Foram encontradas apenas {len(frequencias_encontradas)} frações.")
            print("Dica: Se o número for menor que 8, o SofaScore não carregou todos os cards de H2H.")

    except Exception as e:
        print(f"🚨 LOG ERRO CRÍTICO: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Testando com Como x Roma
    testar_analise_detalhada("Como", "AS Roma")
