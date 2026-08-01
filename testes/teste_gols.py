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
    # URL do jogo Remo x Santos
    url_teste = "https://www.flashscore.com.br/jogo/futebol/remo-2i0B6Zul/santos-n3QdnjFB/h2h/total/"
    t1_nome, t2_nome = "Remo", "Santos"
    
    # 🔗 Monta as URLs diretas de CASA e FORA
    url_limpa = url_teste.rstrip("/")
    if "/h2h" in url_limpa:
        url_base = url_limpa.split("/h2h")[0] + "/h2h"
    else:
        url_base = url_limpa + "/h2h"

    url_casa = f"{url_base}/casa/"
    url_fora = f"{url_base}/fora/"

    driver = configurar_driver()
    print(f"\n🚀 Iniciando teste real com URLs diretas: {t1_nome} x {t2_nome}")
    print(f"🔗 URL Casa: {url_casa}")
    print(f"🔗 URL Fora: {url_fora}")
    
    try:
        stats = {
            "casa_15": 0, "casa_25": 0, "casa_35_under": 0, "casa_45_under": 0,
            "fora_15": 0, "fora_25": 0, "fora_35_under": 0, "fora_45_under": 0,
            "ultimo_gols_casa": 0, "ultimo_gols_fora": 0,
            "h2h_placar_1": "" 
        }

        # --- PARTE 1: MANDANTE JOGANDO EM CASA (/h2h/casa/) ---
        print(f"\n📊 Analisando jogos isolados de CASA ({t1_nome}):")
        driver.get(url_casa)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        secoes_casa = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        if secoes_casa:
            linhas_casa = secoes_casa[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for i, linha in enumerate(linhas_casa):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    print(f"   Jogo {i+1} (Em Casa): Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0:
                        stats["ultimo_gols_casa"] = total
                    
                    if total > 1.5: stats["casa_15"] += 1
                    if total > 2.5: stats["casa_25"] += 1
                    if total <= 3: stats["casa_35_under"] += 1
                    if total <= 4: stats["casa_45_under"] += 1

        # --- PARTE 2: VISITANTE JOGANDO FORA (/h2h/fora/) ---
        print(f"\n📊 Analisando jogos isolados de FORA ({t2_nome}):")
        driver.get(url_fora)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__section")))
        
        secoes_fora = driver.find_elements(By.CSS_SELECTOR, ".h2h__section")
        if secoes_fora:
            linhas_fora = secoes_fora[0].find_elements(By.CSS_SELECTOR, ".h2h__row")[:5]
            for i, linha in enumerate(linhas_fora):
                res_texto = linha.find_element(By.CSS_SELECTOR, ".h2h__result").text
                numeros = re.findall(r'\d+', res_texto)
                
                if len(numeros) >= 2:
                    g1, g2 = int(numeros[0]), int(numeros[1])
                    total = g1 + g2
                    print(f"   Jogo {i+1} (Fora): Placar {g1}-{g2} | Total: {total} gols")
                    
                    if i == 0:
                        stats["ultimo_gols_fora"] = total
                    
                    if total > 1.5: stats["fora_15"] += 1
                    if total > 2.5: stats["fora_25"] += 1
                    if total <= 3: stats["fora_35_under"] += 1
                    if total <= 4: stats["fora_45_under"] += 1

        # --- PARTE 3: CONFRONTO DIRETO H2H (Pegando da tabela 3 se disponível) ---
        if secoes_fora and len(secoes_fora) >= 3:
            print("\n⚔️ Analisando o histórico de Confronto Direto (H2H):")
            linhas_h2h = secoes_fora[2].find_elements(By.CSS_SELECTOR, ".h2h__row")
            if linhas_h2h:
                ultimo_confronto_placar = linhas_h2h[0].find_element(By.CSS_SELECTOR, ".h2h__result").text
                stats["h2h_placar_1"] = ultimo_confronto_placar
                print(f"   ➔ Último jogo do H2H capturado: '{ultimo_confronto_placar}'")
            else:
                print("   ⚠️ Nenhuma linha de H2H encontrada na Tabela 3.")
        else:
            print("\n⚠️ Tabela de confronto direto (H2H) não encontrada diretamente nesta visão.")

        print("\n--- RESUMO DO DICIONÁRIO EXTRAÍDO ---")
        print(stats)

        # --- PARTE 4: SIMULAÇÃO E LOGS DE VALIDAÇÃO DOS MERCADOS ---
        print("\n--- LOGS DETALHADOS DE VALIDAÇÃO DOS MERCADOS DE GOLS ---")
        u_h2h = stats["h2h_placar_1"]
        
        mercados_para_validar = [
            (4.5, "-4.5 Under"), 
            (3.5, "-3.5 Under"), 
            (1.5, "+1.5 Over"), 
            (2.5, "+2.5 Over")
        ]
        
        for alvo, nome_m in mercados_para_validar:
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
            p2_passou = gols.verificar_ultimo_jogo(u_h2h, alvo) if hasattr(gols, 'verificar_ultimo_jogo') else True
            
            status_p1 = "✅ PASSOU" if p1_passou else "❌ REPROVOU"
            status_p2 = "✅ PASSOU" if p2_passou else "❌ REPROVOU"
            
            print(f"📌 Mercado {nome_m}:")
            print(f"   -> Passo 1 (Min 4/5?): {status_p1} | Casa: {c_val}/5, Fora: {f_val}/5")
            print(f"   -> Passo 2 (H2H válido?): {status_p2} | Placar H2H: '{u_h2h}'")

        print("\n--- RESULTADO FINAL DO MÓDULO GOLS.PY ---")
        res_gols = gols.verificar_gols(stats)
        
        if not res_gols:
            print("❌ Módulo GOLS.PY não aprovou nenhuma entrada de gols para este jogo.")
        else:
            for r in res_gols:
                print(f"💰 PALPITE EMITIDO: {r.get('texto', r)} [Tipo/Chave: {r.get('chave', 'N/A')}]")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    finally:
        driver.quit()
        print("\n🏁 Teste finalizado.")

if __name__ == "__main__":
    testar_jogo_especifico()
                
