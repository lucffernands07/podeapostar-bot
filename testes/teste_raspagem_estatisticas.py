import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def verificar_chutes_totais(s):
    """
    Regra de Chutes Totais do Jogo (Formato Decimal Livre)
    Retorna a média esperada calculada dos últimos 5 jogos para livre escolha na Betano.
    """
    if not isinstance(s, dict):
        return []

    media_m = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_v = float(s.get("visitante_media_chutes_fora", 0) or 0)

    if media_m == 0 or media_v == 0:
        return []

    media_esperada = media_m + media_v

    mercados_aprovados = []
    mercados_aprovados.append({
        "mercado": f"Chutes Totais no Jogo: {media_esperada:.1f}",
        "tipo": "CHUTES_JOGO_TOTAL"
    })

    return mercados_aprovados

def extrair_estatisticas_partida(driver, url_jogo):
    """
    Navega para a aba de estatísticas do jogo individual e extrai o total de finalizações.
    """
    chutes_casa = 0
    chutes_fora = 0
    
    try:
        if "?mid=" in url_jogo:
            url_stats = f"{url_jogo.split('?mid=')[0].rstrip('/')}/resumo/estatisticas/total/"
        else:
            url_stats = f"{url_jogo.split('/#')[0].rstrip('/')}/resumo/estatisticas/total/"
            
        driver.get(url_stats)
        time.sleep(2.0)
        
        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
        achou_cartoes_ancora = False
        
        for idx, span in enumerate(todos_spans):
            texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
            
            if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                achou_cartoes_ancora = True
                
            if not achou_cartoes_ancora and any(termo in texto_elemento for termo in ["FINALIZAÇÕES", "REMATES", "SHOTS"]):
                if idx > 0 and (idx + 1) < len(todos_spans):
                    import re
                    val_casa_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                    val_fora_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                    chutes_casa = int(re.search(r'\d+', val_casa_str).group()) if re.search(r'\d+', val_casa_str) else 0
                    chutes_fora = int(re.search(r'\d+', val_fora_str).group()) if re.search(r'\d+', val_fora_str) else 0
                    break
    except Exception as e:
        print(f"  ⚠️ Erro ao raspar estatísticas do jogo: {e}")
        
    return chutes_casa, chutes_fora

def rodar_teste_chutes_totais_com_urls():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URL Base informada
    url_base_h2h = "https://www.flashscore.com.br/jogo/futebol/argentina-f9OppQjp/inglaterra-j9N9ZNFA/h2h/total/"
    
    # Constrói dinamicamente as URLs de casa e fora com base na URL base fornecida
    url_casa = url_base_h2h.replace("/h2h/total/", "/h2h/casa/")
    url_fora = url_base_h2h.replace("/h2h/total/", "/h2h/fora/")
    
    print("\n🚀 INICIANDO TESTE ISOLADO: URLs SEPARADAS E MÉDIA DE CHUTES TOTAIS\n" + "="*80)
    print(f"1. URL CASA: {url_casa}")
    print(f"2. URL FORA: {url_fora}")
    print("-" * 80)
    
    chutes_mandante_h2h = []
    chutes_visitante_h2h = []

    try:
        # --- ETAPA 1: Coleta segura das URLs de CASA do Mandante ---
        print("\n🏠 Acessando aba de CASA do Mandante...")
        driver.get(url_casa)
        time.sleep(4.0)
        
        urls_mandante_links = []
        blocos_mandante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        if blocos_mandante:
            linhas_mandante = blocos_mandante[0].find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")[:5]
            for linha in linhas_mandante:
                href = linha.get_attribute("href")
                if href:
                    urls_mandante_links.append(href)

        # Itera puramente sobre as strings de links salvos
        for href in urls_mandante_links:
            c_casa, _ = extrair_estatisticas_partida(driver, href)
            if c_casa > 0:
                chutes_mandante_h2h.append(c_casa)
                print(f"   • Jogo: {href} ➔ Chutes Mandante: {c_casa}")

        # --- ETAPA 2: Coleta segura das URLs de FORA do Visitante ---
        print("\n✈️ Acessando aba de FORA do Visitante...")
        driver.get(url_fora)
        time.sleep(4.0)
        
        urls_visitante_links = []
        blocos_visitante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        if len(blocos_visitante) >= 1:
            alvo_bloco = blocos_visitante[1] if len(blocos_visitante) > 1 else blocos_visitante[0]
            linhas_visitante = alvo_bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")[:5]
            for linha in linhas_visitante:
                href = linha.get_attribute("href")
                if href:
                    urls_visitante_links.append(href)

        # Itera puramente sobre as strings de links salvos
        for href in urls_visitante_links:
            _, c_fora = extrair_estatisticas_partida(driver, href)
            if c_fora > 0:
                chutes_visitante_h2h.append(c_fora)
                print(f"   • Jogo: {href} ➔ Chutes Visitante: {c_fora}")

        # Cálculo das Médias
        media_m = round(sum(chutes_mandante_h2h) / len(chutes_mandante_h2h), 2) if chutes_mandante_h2h else 0.0
        media_v = round(sum(chutes_visitante_h2h) / len(chutes_visitante_h2h), 2) if chutes_visitante_h2h else 0.0

        stats_teste = {
            "mandante_media_chutes_casa": media_m,
            "visitante_media_chutes_fora": media_v
        }

        # Aplicação da regra de chutes totais
        resultado_mercados = verificar_chutes_totais(stats_teste)
        
        print("\n" + "="*80)
        print("3. RESULTADO DA MÉDIA DE CHUTES TOTAIS:")
        if resultado_mercados:
            for item in resultado_mercados:
                print(f"   ✅ {item['mercado']}")
        else:
            print("   ⚠️ Média parcial zerada ou dados insuficientes recolhidos no momento.")
            print(f"   • Média Calculada Mandante (Casa): {media_m}")
            print(f"   • Média Calculada Visitante (Fora): {media_v}")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de URLs: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE")

if __name__ == "__main__":
    rodar_teste_chutes_totais_com_urls()
            
