import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- CONFIGURAÇÃO --- #
ZENROWS_KEY = os.getenv('ZENROWS_KEY')
PROXY = f"http://{ZENROWS_KEY}:@proxy.zenrows.com:8001"

def configurar_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument(f'--proxy-server={PROXY}')
    return webdriver.Chrome(options=options)

def realizar_analise():
    driver = configurar_driver()
    try:
        # 1. ACESSO INICIAL
        print("🚀 Acessando SofaScore para buscar jogos de hoje...")
        driver.get("https://www.sofascore.com/pt/")
        time.sleep(5) # Espera carregar a lista
        
        # Simulação de captura de jogos (links)
        jogos_links = ["url_jogo_1", "url_jogo_2"] # Aqui o robô pegaria os links reais
        print(f"✅ {len(jogos_links)} jogos encontrados na lista de hoje.")
        print("-" * 50)

        for link in jogos_links:
            # 2. LOG DE ACESSO AO JOGO
            nome_jogo = "Juventus vs Genoa" # Exemplo capturado
            print(f"🔍 Analisando: {nome_jogo}")
            
            # 3. LOG DOS ÚLTIMOS 5 JOGOS (CONSISTÊNCIA)
            # Aqui o robô extrai os resultados das bolinhas (V, E, D ou Gols)
            resumo_t1 = [1, 1, 1, 1, 0] # 1 = bateu mercado, 0 = não bateu
            resumo_t2 = [1, 1, 1, 1, 1]
            
            print(f"   📊 Consistência (últimos 5):")
            print(f"      - Time Casa: {sum(resumo_t1)}/5 encontrado")
            print(f"      - Time Fora: {sum(resumo_t2)}/5 encontrado")

            # 4. LOG DE CHUTES (MÉDIA 5 JOGOS INDIVIDUAL)
            # O robô entra na aba de estatísticas e pega os 'Shots on Target'
            chutes_t1 = [5, 6, 4, 7, 4] 
            chutes_t2 = [4, 5, 3, 6, 5]
            media_t1 = sum(chutes_t1) / 5
            media_t2 = sum(chutes_t2) / 5
            
            print(f"   🎯 Média de Chutes no Gol (Individual - 5 jogos):")
            print(f"      - {nome_jogo.split(' vs ')[0]}: {media_t1:.1f}")
            print(f"      - {nome_jogo.split(' vs ')[1]}: {media_t2:.1f}")

            # 5. DECISÃO DO BILHETE
            if sum(resumo_t1) >= 4 and sum(resumo_t2) >= 4:
                soma_chutes = media_t1 + media_t2
                print(f"   ✅ APROVADO: Soma de chutes {soma_chutes:.1f} -> Projeção de Escanteios ativa.")
            else:
                print(f"   ❌ REPROVADO: Fora da regra 4/5 ou 5/5.")
            
            print("-" * 30)

    except Exception as e:
        print(f"❌ Erro durante o acesso: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    realizar_analise()
