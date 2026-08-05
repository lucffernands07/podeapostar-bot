import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re

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
        time.sleep(2.5)
        
        todos_spans = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01']")
        
        for idx, span in enumerate(todos_spans):
            texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
            
            if any(termo in texto_elemento for termo in ["FINALIZAÇÕES", "REMATES", "SHOTS"]):
                if idx > 0 and (idx + 1) < len(todos_spans):
                    val_casa_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                    val_fora_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                    
                    match_c = re.search(r'\d+', val_casa_str)
                    match_f = re.search(r'\d+', val_fora_str)
                    
                    chutes_casa = int(match_c.group()) if match_c else 0
                    chutes_fora = int(match_f.group()) if match_f else 0
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
    
    url_base_h2h = "https://www.flashscore.com.br/jogo/futebol/fortaleza-42FbPIs2/palmeiras-hMn9FTbH/h2h/total/"
    
    url_casa = url_base_h2h.replace("/h2h/total/", "/h2h/casa/")
    url_fora = url_base_h2h.replace("/h2h/total/", "/h2h/fora/")
    
    print("\n🚀 INICIANDO TESTE ISOLADO: FORTALEZA X PALMEIRAS (5 JOGOS CADA)\n" + "="*80)
    print(f"1. URL CASA: {url_casa}")
    print(f"2. URL FORA: {url_fora}")
    print("-" * 80)
    
    chutes_mandante_h2h = []
    chutes_visitante_h2h = []

    try:
        # ==========================================
        # PASSO 1: Coletar os links dos 5 jogos do Mandante (CASA)
        # ==========================================
        print("\n🏠 Acessando aba de CASA do Mandante (Fortaleza)...")
        driver.get(url_casa)
        time.sleep(4.0)
        
        urls_mandante_links = []
        blocos_mandante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        if blocos_mandante:
            # Pega estritamente até 5 linhas da seção de casa
            linhas_mandante = blocos_mandante[0].find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")[:5]
            for linha in linhas_mandante:
                href = linha.get_attribute("href")
                if href:
                    urls_mandante_links.append(href)

        print(f"   📌 Encontrados {len(urls_mandante_links)} jogos do Mandante em casa. Raspando estatísticas...")
        for idx, href in enumerate(urls_mandante_links, start=1):
            c_casa, _ = extrair_estatisticas_partida(driver, href)
            if c_casa > 0:
                chutes_mandante_h2h.append(c_casa)
                print(f"   • [{idx}/5] Jogo: {href} ➔ Chutes Mandante: {c_casa}")

        # ==========================================
        # PASSO 2: Coletar os links dos 5 jogos do Visitante (FORA)
        # ==========================================
        print("\n✈️ Acessando aba de FORA do Visitante (Palmeiras)...")
        driver.get(url_fora)
        time.sleep(4.0)
        
        urls_visitante_links = []
        blocos_visitante = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        if len(blocos_visitante) >= 2:
            # Na aba /h2h/fora/, o segundo bloco costuma focar nos jogos fora do visitante
            linhas_visitante = blocos_visitante[1].find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")[:5]
            for linha in linhas_visitante:
                href = linha.get_attribute("href")
                if href:
                    urls_visitante_links.append(href)

        print(f"   📌 Encontrados {len(urls_visitante_links)} jogos do Visitante fora. Raspando estatísticas...")
        for idx, href in enumerate(urls_visitante_links, start=1):
            _, c_fora = extrair_estatisticas_partida(driver, href)
            if c_fora > 0:
                chutes_visitante_h2h.append(c_fora)
                print(f"   • [{idx}/5] Jogo: {href} ➔ Chutes Visitante: {c_fora}")

        # ==========================================
        # PASSO 3: Cálculo das Médias Finais
        # ==========================================
        media_m = round(sum(chutes_mandante_h2h) / len(chutes_mandante_h2h), 2) if chutes_mandante_h2h else 0.0
        media_v = round(sum(chutes_visitante_h2h) / len(chutes_visitante_h2h), 2) if chutes_visitante_h2h else 0.0

        stats_teste = {
            "mandante_media_chutes_casa": media_m,
            "visitante_media_chutes_fora": media_v
        }

        resultado_mercados = verificar_chutes_totais(stats_teste)
        
        print("\n" + "="*80)
        print("3. RESULTADO DA MÉDIA DE CHUTES TOTAIS:")
        print(f"   • Média Calculada Mandante (Casa): {media_m} (Baseado em {len(chutes_mandante_h2h)} jogos)")
        print(f"   • Média Calculada Visitante (Fora): {media_v} (Baseado em {len(chutes_visitante_h2h)} jogos)")
        
        if resultado_mercados:
            for item in resultado_mercados:
                print(f"   ✅ {item['mercado']}")
        else:
            print("   ⚠️ Dados insuficientes para gerar a média.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de URLs: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE")

if __name__ == "__main__":
    rodar_teste_chutes_totais_com_urls()
    
