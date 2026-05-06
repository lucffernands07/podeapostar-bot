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

# --- CONFIGURAÇÕES DE CAMINHO ---
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
    return [] if "pendentes" in caminho else {"stats": {}}

def salvar_json(dados, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
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
    log(1, "Iniciando captura no Flashscore...")
    driver = configurar_driver()
    resultados = {}
    try:
        driver.get("https://www.flashscore.com.br/")
        wait = WebDriverWait(driver, 30)
        
        # 1. Clicar em ENCERRADOS usando o container .zone__inner
        log(2, "Buscando botão ENCERRADOS no carrossel...")
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".zone__inner")))
        # Busca o botão dentro do carrossel ignorando maiúsculas
        btn_enc = container.find_element(By.XPATH, ".//div[contains(translate(text(), 'encerrados', 'ENCERRADOS'), 'ENCERRADOS')]")
        driver.execute_script("arguments[0].click();", btn_enc)
        time.sleep(3)
        
        # 2. Abrir Calendário e voltar para ontem
        log(3, "Acessando calendário para pegar data de ontem...")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='wcl-dayPickerButton']"))).click()
        seta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "path.action-navigation-arrow-left")))
        btn_seta = seta.find_element(By.XPATH, "./..")
        driver.execute_script("arguments[0].click();", btn_seta)
        time.sleep(7)

        # 3. Extrair os placares
        log(4, "Lendo jogos encerrados...")
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
        log(5, f"Capturados {len(resultados)} jogos.")
    finally:
        driver.quit()
    return resultados

def main():
    log(0, "Iniciando Processamento de Ranking")
    pendentes = carregar_json(PATH_PENDENTES)
    if not pendentes:
        log("AVISO", "O arquivo pendentes.json está vazio. Nada para validar.")
        return

    resultados_site = capturar_resultados()
    db = carregar_json(PATH_DB)
    stats = db.get("stats", {})
    
    atualizados = 0
    log(6, "Cruzando dados e atualizando estatísticas...")
    
    for jogo in pendentes:
        # Nome do confronto no seu listão (Limpando parênteses de países se houver)
        nome_casa = jogo['time_casa'].split('(')[0].strip().lower()
        nome_fora = jogo['time_fora'].split('(')[0].strip().lower()
        chave = f"{nome_casa} x {nome_fora}"
        
        # Procura no dicionário de resultados (busca parcial para evitar erros de nomes longos)
        res = next((v for k, v in resultados_site.items() if nome_casa in k and nome_fora in k), None)
        
        if res:
            deu_green = validar_palpite(jogo['mercado'], res['c'], res['f'])
            m_rank = jogo['mercado_ranking']
            
            if m_rank not in stats:
                stats[m_rank] = {"green": 0, "red": 0}
            
            if deu_green:
                stats[m_rank]['green'] += 1
            else:
                stats[m_rank]['red'] += 1
            atualizados += 1

    db["stats"] = stats
    salvar_json(db, PATH_DB)
    # Limpa a lista de pendentes após o sucesso
    salvar_json([], PATH_PENDENTES)
    log("FIM", f"Ranking atualizado! {atualizados} jogos processados com sucesso.")

if __name__ == "__main__":
    main()
    
