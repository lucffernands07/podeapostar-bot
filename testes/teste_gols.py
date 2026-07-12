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

# Ajuste para importar módulos da pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mercados import gols

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

def testar_jogo_especifico():
    # URL real do jogo Cruzeiro x Fluminense enviada por você
    url_teste = "https://www.flashscore.com.br/jogo/futebol/cruzeiro-0SwtclaU/fluminense-EV9L3kU4/h2h/total/"
    t1_nome, t2_nome = "Cruzeiro", "Fluminense"
    
    driver = configurar_driver()
    print(f"\n🚀 Iniciando teste real: {t1_nome} x {t2_nome}")
    
    try:
        driver.get(url_teste)
        wait = WebDriverWait(driver, 15)
        time.sleep(4) # Tempo de segurança para renderização das tabelas
        
        stats = {
            "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0, # 🟢 Adicionado casa_35_under
            "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0, # 🟢 Adicionado fora_35_under
            "ultimo_gols_casa": 0, "ultimo_gols_fora": 0,
            "h2h_placar_1": "" 
        }

        secoes = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        
        # --- PARTE 1: RASPAR ÚLTIMOS JOGOS ISOLADOS (CASA E FORA) ---
        for idx, secao in enumerate(secoes[:2]): 
            prefixo = "casa" if idx == 0 else "fora"
            nome_time = t1_nome if idx == 0 else t2_nome
            print(f"\n📊 Analisando jogos isolados de {prefixo.upper()} ({nome_time}):")
            
            linhas = secao.find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            
            for i, linha in enumerate(linhas):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    print(f"   Jogo {i+1}: Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0:
                        stats[f"ultimo_gols_{prefixo}"] = total
                    
                    if total > 1.5: stats[f"{prefixo}_15"] += 1
                    if total > 2.5: stats[f"{prefixo}_25"] += 1
                    if total <= 3: stats[f"{prefixo}_35_under"] += 1 # 🟢 Nova contagem de -3.5 gols
                    if total <= 4: stats[f"{prefixo}_45_under"] += 1

        # --- PARTE 2: RASPAR O ÚLTIMO CONFRONTO DIRETO (H2H TABELA 3) ---
        if len(secoes) >= 3:
            print("\n⚔️ Analisando o histórico de Confronto Direto (H2H):")
            linhas_h2h = secoes[2].find_elements(By.CSS_SELECTOR, ".h2h__row")
            if linhas_h2h:
                ultimo_confronto_placar = linhas_h2h[0].find_element(By.CSS_SELECTOR, ".h2h__result").text
                stats["h2h_placar_1"] = ultimo_confronto_placar
                print(f"   ➔ Último jogo do H2H capturado: '{ultimo_confronto_placar}'")
            else:
                print("   ⚠️ Nenhuma linha de H2H encontrada na Tabela 3.")
        else:
            print("   ⚠️ Tabela 3 de H2H não está disponível na página.")

        print("\n--- RESUMO DO DICIONÁRIO ENVIADO ---")
        print(stats)

        # --- PARTE 3: SIMULAÇÃO E LOGS DE VALIDAÇÃO DOS MERCADOS ---
        print("\n--- LOGS DETALHADOS DE VALIDAÇÃO (PASSO A PASSO) ---")
        u_h2h = stats["h2h_placar_1"]
        
        # Lista atualizada com o novo mercado de 3.5 gols incluído no loop de log
        mercados_para_validar = [
            (4.5, "-4.5 Under"), 
            (3.5, "-3.5 Under"), # 🟢 Novo mercado mapeado aqui
            (1.5, "+1.5 Over"), 
            (2.5, "+2.5 Over")
        ]
        
        for alvo, nome_m in mercados_para_validar:
            # Tratamento dinâmico do nome das chaves com base na sua estrutura
            if alvo in [3.5, 4.5]:
                pref_c = "casa_35_under" if alvo == 3.5 else "casa_45_under"
                pref_f = "fora_35_under" if alvo == 3.5 else "fora_45_under"
            else:
                pref_c = f"casa_{str(alvo).replace('.','')}"
                pref_f = f"fora_{str(alvo).replace('.','')}"
            
            c_val = stats.get(pref_c, 0)
            f_val = stats.get(pref_f, 0)
            
            # Validação do passo 1 (Mínimo 4/5)
            p1_passou = c_val >= 4 and f_val >= 4
            
            # Validação do passo 2 (H2H bate mercado)
            p2_passou = gols.verificar_ultimo_jogo(u_h2h, alvo)
            
            status_p1 = "✅ PASSOU" if p1_passou else "❌ REPROVOU"
            status_p2 = "✅ PASSOU" if p2_passou else "❌ REPROVOU"
            
            print(f"📌 Mercado {nome_m}:")
            print(f"   -> Passo 1 (Min 4/5?): {status_p1} | Casa: {c_val}/5, Fora: {f_val}/5")
            print(f"   -> Passo 2 (H2H válido?): {status_p2} | Placar H2H: '{u_h2h}'")

        print("\n--- RESULTADO FINAL DO MÓDULO GOLS.PY ---")
        res_gols = gols.verificar_gols(stats)
        
        if not res_gols:
            print("❌ Módulo GOLS.PY não aprovou nenhuma entrada para este jogo.")
        else:
            for r in res_gols:
                print(f"💰 PALPITE EMITIDO PARA O BILHETE: {r['mercado']} [Tipo: {r['tipo']}]")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_jogo_especifico()
        
