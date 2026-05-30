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
    """ Nova Regra: Baseada estritamente na contagem de vitórias do Confronto Direto """
    mercados = []
    
    vitorias_casa = 0
    vitorias_fora = 0
    
    # Varre as 5 variáveis capturadas do H2H
    for i in range(1, 6):
        res_h2h = s.get(f"h2h_res_{i}", "").strip().upper()
        if res_h2h == "CASA":
            vitorias_casa += 1
        elif res_h2h == "FORA":
            vitorias_fora += 1

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
    # 📌 NOVA URL DE TESTE ATUALIZADA
    url_teste = "https://www.flashscore.com.br/jogo/futebol/chapecoense-jcQV3XP6/palmeiras-hMn9FTbH/h2h/total/"
    
    # Definição dos nomes baseados no mando de campo atual
    t1_casa = "Chapecoense"
    t2_fora = "Palmeiras"
    
    driver = configurar_driver()
    print(f"\n🚀 Executando Validação H2H Baseada em Vencedores")
    print(f"🏟️ Jogo Atual: {t1_casa} (Casa) x {t2_fora} (Fora)")
    print(f"🔗 Link de Análise: {url_teste}\n")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        time.sleep(3)
        
        # Dicionário de estatísticas simulando o main do seu bot
        stats = {
            "h2h_res_1": "",
            "h2h_res_2": "",
            "h2h_res_3": "",
            "h2h_res_4": "",
            "h2h_res_5": ""
        }
        
        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # A terceira tabela (índice 2) é sempre o Confronto Direto (H2H) Geral
        if len(secoes) >= 3:
            secao_h2h = secoes[2]
            linhas = secao_h2h.find_elements(By.CSS_SELECTOR, ".h2h__row")
            print(f"🔎 Analisando Tabela 3 (Últimos {len(linhas[:5])} Confrontos Diretos)...")
            
            # Varre no máximo as últimas 5 partidas diretas
            for i, linha in enumerate(linhas[:5]):
                try:
                    time_casa_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__homeParticipant").text.strip()
                    time_fora_h2h = linha.find_element(By.CSS_SELECTOR, ".h2h__awayParticipant").text.strip()
                    
                    # 🚀 Captura o elemento do resultado que possui a classe de vencedor (--winner)
                    # Caso seja um empate, nenhum dos dois terá a classe winner
                    vencedor_elemento = linha.find_elements(By.CSS_SELECTOR, ".h2h__participant.--winner")
                    
                    if vencedor_elemento:
                        nome_vencedor = vencedor_elemento[0].text.strip().lower()
                        
                        # Compara quem venceu o jogo com as equipes do confronto de hoje
                        if t1_casa.lower() in nome_vencedor:
                            stats[f"h2h_res_{i+1}"] = "CASA"
                            print(f"   ⚔️ Linha {i+1}: {time_casa_h2h} vs {time_fora_h2h} ➔ Vencedor: {t1_casa} (Marcar CASA)")
                        elif t2_fora.lower() in nome_vencedor:
                            stats[f"h2h_res_{i+1}"] = "FORA"
                            print(f"   ⚔️ Linha {i+1}: {time_casa_h2h} vs {time_fora_h2h} ➔ Vencedor: {t2_fora} (Marcar FORA)")
                        else:
                            stats[f"h2h_res_{i+1}"] = "OUTRO"
                            print(f"   ⚔️ Linha {i+1}: {time_casa_h2h} vs {time_fora_h2h} ➔ Vencedor: {vencedor_elemento[0].text} (Outro time)")
                    else:
                        stats[f"h2h_res_{i+1}"] = "EMPATE"
                        print(f"   ⚔️ Linha {i+1}: {time_casa_h2h} vs {time_fora_h2h} ➔ Resultado: EMPATE")
                except Exception as line_err:
                    print(f"   ⚠️ Erro ao processar linha {i+1}: {line_err}")
                    stats[f"h2h_res_{i+1}"] = "ERRO"
        else:
            print("🟥 Erro: Tabela 3 de Confrontos Diretos não encontrada na página.")
            return

        # Executa a nova regra matemática passando o dicionário preenchido
        mercados_aprovados, v_c, v_f = verificar_chance_dupla(stats)

        print("\n" + "="*75)
        print(f"🔬 CONSOLIDADO FINAL DA NOVA REGRA H2H")
        print(f"   [DADOS RASPADOS]: {list(stats.values())}")
        print(f"   📊 Total Vitórias Mandante Atual ({t1_casa}): {v_c}")
        print(f"   📊 Total Vitórias Visitante Atual ({t2_fora}): {v_f}")
        print("-"*75)
        if mercados_aprovados:
            print(f"   🟩 PROPOSTA EMITIDA: {mercados_aprovados}")
        else:
            print(f"   🟥 BLOQUEADO: Nenhum time atingiu o critério mínimo (3, 4 ou 5 Vitórias).")
        print("="*75 + "\n")

    except Exception as e:
        print(f"❌ Erro Crítico no Teste: {e}")
    finally:
        driver.quit()
        print("🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_nova_logica_h2h()
        
