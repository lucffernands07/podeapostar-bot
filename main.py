import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    # Desativamos o headless para você ver o robô trabalhando
    # options.add_argument("--headless") 
    options.add_argument("--window-size=1366,768")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def log_diagnostico(driver, id_jogo_h2h):
    url = f"https://www.flashscore.com.br/jogo/{id_jogo_h2h}/#/resumo-de-jogo/estatisticas-de-jogo"
    print(f"\n--- [LOG] Abrindo detalhe do jogo: {id_jogo_h2h} ---")
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        print("--- [LOG] Aguardando botão 'Estatísticas'...")
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Estatísticas')]"))
        )
        print("--- [LOG] Botão encontrado. Clicando via JS...")
        driver.execute_script("arguments[0].click();", btn)
        
        print("--- [LOG] Aguardando 4 segundos para renderização dos gráficos...")
        time.sleep(4)
        
        # Diagnóstico de texto bruto
        print("--- [LOG] Varrendo categorias de estatísticas disponíveis:")
        categorias = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='wcl-statistics-category']")
        encontrou_escanteio = False
        
        for cat in categorias:
            texto = cat.text.replace('\n', ' ')
            print(f"    > Encontrado: {texto}")
            if "Escanteios" in texto:
                encontrou_escanteio = True
                nums = re.findall(r'\d+', texto)
                print(f"    ✅ SUCESSO: Escanteios detectados -> Casa: {nums[0]} | Fora: {nums[1]}")
        
        if not encontrou_escanteio:
            print("    ❌ FALHA: A palavra 'Escanteios' não foi lida na lista acima.")
            
    except Exception as e:
        print(f"    ❌ ERRO CRÍTICO: {str(e)}")
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def main_teste():
    driver = configurar_driver()
    # ID real do jogo Defensa y Justicia x Boca Juniors (baseado no histórico recente)
    # Nota: Se o jogo mudar de ID, você pode pegar o ID atual na URL do Flashscore
    id_principal = "ne5y23mR" 
    
    try:
        print(f"🚀 Iniciando Teste de Diagnóstico para Defensa y Justicia x Boca")
        driver.get(f"https://www.flashscore.com.br/jogo/{id_principal}/#/h2h/overall")
        time.sleep(5)
        
        print("--- [LOG] Coletando IDs dos últimos jogos no H2H...")
        linhas = driver.find_elements(By.CSS_SELECTOR, ".h2h__row")[:3] # Testaremos apenas os 3 primeiros para ser rápido
        ids_teste = [l.get_attribute("id").split('_')[-1] for l in linhas]
        
        print(f"--- [LOG] IDs encontrados para teste: {ids_teste}")
        
        for id_h2h in ids_teste:
            log_diagnostico(driver, id_h2h)
            
    finally:
        print("\n--- TESTE FINALIZADO ---")
        driver.quit()

if __name__ == "__main__":
    main_teste()
