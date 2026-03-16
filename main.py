import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def configurar_browser():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def testar_logica_antiga_no_link_direto(url_jogo):
    driver = configurar_browser()
    # Adicionando a aba matches para cair direto onde estão as frações
    url_final = url_jogo + "#tab:matches"
    
    print(f"\n🚀 --- EXECUTANDO LÓGICA ANTIGA NO LINK ---")
    print(f"🔗 Alvo: {url_final}")
    
    try:
        driver.get(url_final)
        
        # O código antigo esperava um tempo para os cards carregarem
        print("⏳ Aguardando 12 segundos (Carga dos cards)...")
        time.sleep(12) 

        # --- EXATAMENTE COMO NO CÓDIGO ANTIGO ---
        texto_bruto = driver.find_element(By.TAG_NAME, "body").text
        
        frequencias = []
        # Scanner de Escanteios usando re.finditer
        matches = re.finditer(r"10\.5\s+escanteios", texto_bruto, re.IGNORECASE)
        
        print("\n🔍 Escaneando texto bruto por padrões '10.5 escanteios'...")
        
        for i, m in enumerate(matches, 1):
            # Pega os 50 caracteres após o término da palavra "escanteios"
            trecho_apos = texto_bruto[m.end() : m.end() + 50]
            
            # Busca a fração (\d+)/(\d+)
            frequencia = re.search(r"(\d+)/(\d+)", trecho_apos)
            
            if frequencia:
                num, den = int(frequencia.group(1)), int(frequencia.group(2))
                perc = (num / den) * 100
                frequencias.append(perc)
                print(f"✅ Encontrado na posição {i}: {num}/{den} ({perc:.1f}%)")
            else:
                print(f"⚠️ Posição {i}: Termo encontrado, mas sem fração nos 50 caracteres seguintes.")

        # --- AVALIAÇÃO DA REGRA ANTIGA ---
        print("\n📊 --- RESUMO DAS FREQUÊNCIAS ENCONTRADAS ---")
        print(f"Total de frações capturadas: {len(frequencias)}")
        
        if len(frequencias) >= 2:
            # O código antigo usava as duas primeiras posições capturadas
            f1 = frequencias[0]
            f2 = frequencias[1]
            media = (f1 + f2) / 2
            
            print(f"1ª Fração: {f1:.1f}%")
            print(f"2ª Fração: {f2:.1f}%")
            print(f"Média das duas primeiras: {media:.1f}%")
            
            if f1 >= 90 and f2 >= 90:
                print("🔥 RESULTADO: Menos de 10.5 (PRIORITÁRIO)")
            elif media >= 80:
                print("✅ RESULTADO: Menos de 10.5 (NORMAL)")
            else:
                print("❌ RESULTADO: Não atinge os requisitos mínimos.")
        else:
            print("❌ ERRO: Não foram encontradas pelo menos 2 frações de 10.5 escanteios.")

    except Exception as e:
        print(f"🚨 ERRO CRÍTICO: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    # URL que descobrimos para Lazio x Milan
    url_lazio_milan = "https://www.sofascore.com/pt/football/match/lazio-milan/RdbsZdb#id:13981707"
    testar_logica_antiga_no_link_direto(url_lazio_milan)
            
