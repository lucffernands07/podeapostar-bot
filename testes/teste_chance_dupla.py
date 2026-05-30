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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def verificar_chance_dupla(s):
    """ Nova Regra Interna Baseada estritamente na Contagem do H2H """
    mercados = []
    
    vitorias_casa = s.get("h2h_vitorias_t1", 0)
    vitorias_fora = s.get("h2h_vitorias_t2", 0)

    # --- REGRA 1X (MANDANTE) ---
    if vitorias_casa == 3:
        mercados.append("1X (70%)")
    elif vitorias_casa == 4:
        mercados.append("1X (85%)")
    elif vitorias_casa == 5:
        mercados.append("1X (100%)")
    
    # --- REGRA 2X (VISITANTE) ---
    if vitorias_fora == 3:
        mercados.append("2X (70%)")
    elif vitorias_fora == 4:
        mercados.append("2X (85%)")
    elif vitorias_fora == 5:
        mercados.append("2X (100%)")
            
    return mercados, vitorias_casa, vitorias_fora

def testar_nova_logica_h2h():
    # URL estável do confronto direto para análise
    url_teste = "https://www.flashscore.com.br/jogo/futebol/chapecoense-jcQV3XP6/palmeiras-hMn9FTbH/h2h/total/"
    
    # Definição estrita dos times conforme o mando de hoje
    t1_casa = "Chapecoense"
    t2_fora = "Palmeiras"
    
    driver = configurar_driver()
    print(f"\n🚀 Executando Validação H2H Inteligente (Baseada em Gols e Nomes)")
    print(f"🏟️ Jogo de Hoje -> Casa (t1): {t1_casa} | Visitante (t2): {t2_fora}")
    print(f"🔗 Link de Análise: {url_teste}\n")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(3)
        
        # Dicionário mapeando os contadores que seu bot usa
        stats = {
            "h2h_vitorias_t1": 0,  # Vitórias do Mandante de hoje (Chapecoense)
            "h2h_vitorias_t2": 0,  # Vitórias do Visitante de hoje (Palmeiras)
            "h2h_empates": 0,
            "h2h_res_1": "", "h2h_res_2": "", "h2h_res_3": "", "h2h_res_4": "", "h2h_res_5": ""
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        if len(secoes) >= 3:
            secao_h2h = secoes[2]  # Terceira tabela: Confronto Direto Geral
            linhas = secao_h2h.find_elements(By.CSS_SELECTOR, ".h2h__row")
            print(f"🔎 Analisando Tabela 3 (Últimos {len(linhas[:5])} Confrontos Diretos)...")
            
            for i, linha in enumerate(linhas[:5]):
                try:
                    n_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
                    n_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
                    res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text.strip()
                    
                    # Extração matemática dos gols via Regex
                    numeros_placar = re.findall(r'\d+', res_texto)
                    if len(numeros_placar) < 2: continue
                    g1, g2 = int(numeros_placar[0]), int(numeros_placar[1])
                    
                    res_h2h = "EMPATE"
                    
                    # Lógica cega de mando: descobre quem ganhou por gols e cruza com os nomes
                    if g1 > g2:
                        if t1_casa.lower() in n_casa_h2h.lower():
                            res_h2h = "CASA"
                        elif t2_fora.lower() in n_casa_h2h.lower():
                            res_h2h = "FORA"
                    elif g1 < g2:
                        if t1_casa.lower() in n_fora_h2h.lower():
                            res_h2h = "CASA"
                        elif t2_fora.lower() in n_fora_h2h.lower():
                            res_h2h = "FORA"

                    # Alimenta os contadores matemáticos
                    if res_h2h == "CASA":
                        stats["h2h_vitorias_t1"] += 1
                        print(f"   ⚔️ Linha {i+1}: {n_casa_h2h} {g1}-{g2} {n_fora_h2h} ➔ Ganhou: {t1_casa}")
                    elif res_h2h == "FORA":
                        stats["h2h_vitorias_t2"] += 1
                        print(f"   ⚔️ Linha {i+1}: {n_casa_h2h} {g1}-{g2} {n_fora_h2h} ➔ Ganhou: {t2_fora}")
                    else:
                        stats["h2h_empates"] += 1
                        print(f"   ⚔️ Linha {i+1}: {n_casa_h2h} {g1}-{g2} {n_fora_h2h} ➔ Resultado: EMPATE")
                        
                    # Salva nas variáveis sequenciais h2h_res_X
                    stats[f"h2h_res_{i+1}"] = res_h2h

                except Exception as line_err:
                    print(f"   ⚠️ Erro na linha {i+1}: {line_err}")
        else:
            print("🟥 Erro: Tabela 3 não carregou.")
            return

        # Executa a nova regra matemática
        mercados_aprovados, v_c, v_f = verificar_chance_dupla(stats)

        print("\n" + "="*75)
        print(f"🔬 CONSOLIDADO FINAL DA NOVA REGRA H2H")
        print(f"   [MATEAMENTO SEQUENCIAL]: {[stats[f'h2h_res_{x}'] for x in range(1,6)]}")
        print(f"   📊 Total Vitórias Mandante Atual ({t1_casa}): {v_c}")
        print(f"   📊 Total Vitórias Visitante Atual ({t2_fora}): {v_f}")
        print("-"*75)
        if mercados_aprovados:
            print(f"   🟩 PROPOSTA EMITIDA: {mercados_aprovados}")
        else:
            print(f"   🟥 BLOQUEADO: Nenhum atingiu as 3 vitórias mínimas.")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_nova_logica_h2h()
                    
