import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def extrair_primeira_linha(driver, url, mercado_nome):
    print(f"🌐 Acessando {mercado_nome}: {url}", flush=True)
    driver.get(url)
    
    try:
        # Espera a tabela carregar
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-table__row")))
        time.sleep(5) # Delay para garantir o preenchimento dos valores
        
        # Pega a primeiríssima linha da tabela
        linha = driver.find_element(By.CSS_SELECTOR, ".ui-table__row")
        
        # Extrai os dados
        casa = "Desconhecida"
        try:
            casa = linha.find_element(By.TAG_NAME, "img").get_attribute("alt")
        except:
            pass
            
        spans = linha.find_elements(By.TAG_NAME, "span")
        textos_span = [s.text for s in spans if s.text]
        
        resultado = {
            "mercado": mercado_nome,
            "casa": casa,
            "odds": textos_span,
            "texto_bruto": linha.text.replace("\n", " | ")
        }
        return resultado
    except Exception as e:
        return {"mercado": mercado_nome, "erro": str(e)}

def rodar_teste_bingo_total():
    driver = configurar_driver()
    id_jogo = "W8mj7MDD"
    
    # URLs com a lógica do Bingo (mid) aplicada
    urls = {
        "GOLS 1.5": f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/acima-abaixo/tempo-regulamentar/?mid=lfKIYGgU",
        "BTTS": f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/ambos-marcam/tempo-regulamentar/?mid=lfKIYGgU",
        "DP": f"https://www.flashscore.com.br/jogo/futebol/betis-vJbTeCGP/real-madrid-{id_jogo}/odds/double-chance/tempo-regulamentar/?mid=lfKIYGgU"
    }
    
    relatorio = []
    
    try:
        for mercado, link in urls.items():
            dados = extrair_primeira_linha(driver, link, mercado)
            relatorio.append(dados)
            print(f"✅ Capturado: {mercado}", flush=True)
            time.sleep(2) # Pequena pausa entre abas

        print("\n" + "="*50)
        print("📊 DIAGNÓSTICO DAS PRIMEIRAS LINHAS (BINGO)")
        print("="*50)
        for item in relatorio:
            print(json.dumps(item, indent=2, ensure_ascii=False))
            print("-" * 30)
        print("="*50, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    rodar_teste_bingo_total()
    
