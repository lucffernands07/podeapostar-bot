import os
import time
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configurações de Caminho
PATH_DB = "ranking/ranking_db.json"
PATH_PENDENTES = "ranking/pendentes.json"

def log(etapa, mensagem):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 ETAPA {etapa}: {mensagem}")

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

def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [] if "pendentes" in caminho else {}

def salvar_json(dados, caminho):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def validar_palpite(mercado_str, gols_c, gols_f):
    m = mercado_str.lower()
    total = gols_c + gols_f
    if "+1.5" in m: return total >= 2
    if "+2.5" in m: return total >= 3
    if "-4.5" in m: return total <= 4
    if "ambas marcam" in m or "btts" in m: return gols_c > 0 and gols_f > 0
    if "1x" in m: return gols_c >= gols_f
    if "vitoria casa" in m or "vitória casa" in m: return gols_c > gols_f
    if "2x" in m: return gols_f >= gols_c
    return False

def capturar_resultados():
    log(1, "Acessando Flashscore para capturar resultados de ontem...")
    driver = configurar_driver()
    resultados = {}
    try:
        driver.get("https://www.flashscore.com.br/")
        wait = WebDriverWait(driver, 30) # Aumentado para 30s
        
        # Log de segurança para saber se o site abriu certo
        log("INFO", f"Título da página: {driver.title}")

        # Passo 1: Clicar em Encerrados (usando um seletor mais robusto)
        log(2, "Buscando botão de jogos Encerrados...")
        # Tenta encontrar por texto em PT e EN para garantir
        btn_enc = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'ENCERRADOS')] | //div[contains(text(), 'FINISHED')]")))
        driver.execute_script("arguments[0].click();", btn_enc) # Click via JS é mais garantido no Headless
        time.sleep(3)
        
        # Passo 2: Abrir Calendário
        log(3, "Abrindo seletor de data...")
        btn_calendar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='wcl-dayPickerButton']")))
        driver.execute_script("arguments[0].click();", btn_calendar)
        time.sleep(2)

        # Passo 3: Voltar para ontem
        log(4, "Voltando para a data de ONTEM...")
        # Buscamos a seta pela classe da estrutura interna
        seta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "path.action-navigation-arrow-left")))
        # Clicamos no botão que contém esse SVG
        btn_seta = seta.find_element(By.XPATH, "./..")
        driver.execute_script("arguments[0].click();", btn_seta)
        
        log(5, "Aguardando carregamento dos jogos de ontem...")
        time.sleep(8) # Tempo maior para carregar a lista pesada

        eventos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        for ev in eventos:
            try:
                casa = ev.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                fora = ev.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()
                g_c = ev.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                g_f = ev.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()
                
                if g_c != "" and g_f != "":
                    resultados[f"{casa} x {fora}".lower()] = {"c": int(g_c), "f": int(g_f)}
            except: continue
            
        log(6, f"Sucesso! Capturados {len(resultados)} resultados.")
        
    except Exception as e:
        log("ERRO", f"Falha na captura. Print do erro: {str(e)}")
        # Opcional: tirar print da tela em caso de erro para debug (ajuda muito)
        driver.save_screenshot("erro_captura.png")
    finally:
        driver.quit()
    return resultados

def main():
    log(0, "Iniciando Processamento")
    pendentes = carregar_json(PATH_PENDENTES)
    if not pendentes:
        log("FIM", "Nada para processar em pendentes.json")
        return

    resultados_site = capturar_resultados()
    db = carregar_json(PATH_DB)
    stats = db.get("stats", {})
    
    atualizados = 0
    for jogo in pendentes:
        chave = f"{jogo['time_casa']} x {jogo['time_fora']}".lower()
        res = resultados_site.get(chave)
        
        if res:
            deu_green = validar_palpite(jogo['mercado'], res['c'], res['f'])
            m_rank = jogo['mercado_ranking']
            
            if m_rank not in stats: stats[m_rank] = {"green": 0, "red": 0}
            
            if deu_green: stats[m_rank]['green'] += 1
            else: stats[m_rank]['red'] += 1
            atualizados += 1

    db["stats"] = stats
    salvar_json(db, PATH_DB)
    salvar_json([], PATH_PENDENTES) # Limpa pendentes
    log("FIM", f"Processo concluído. {atualizados} mercados validados.")

if __name__ == "__main__":
    main()
    
