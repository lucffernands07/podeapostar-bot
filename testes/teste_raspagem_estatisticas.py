import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def formatar_rota_h2h(url_base, sub_rota=""):
    path = url_base.split('?')[0].split('#')[0].rstrip('/')
    for sufixo in ['/overall', '/casa', '/fora']:
        if path.endswith(sufixo):
            path = path[:-len(sufixo)]

    if not path.endswith('/h2h'):
        path = f"{path}/h2h"

    if sub_rota:
        path = f"{path}/{sub_rota}"

    return f"{path}/"

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
    Navega para a aba de estatísticas do jogo individual e extrai o total de finalizações de forma limpa.
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
        
        if len(todos_spans) > 0:
            achou_cartoes_ancora = False
            for idx, span in enumerate(todos_spans):
                texto_elemento = driver.execute_script("return arguments[0].textContent;", span).strip().upper()
                
                if texto_elemento in ["CARTÕES AMARELOS", "CARTÃO AMARELO", "YELLOW CARDS", "YELLOW CARD"]:
                    achou_cartoes_ancora = True
                
                if not achou_cartoes_ancora and texto_elemento in ["TOTAL DE FINALIZAÇÕES", "TOTAL SHOTS"]:
                    if idx > 0 and (idx + 1) < len(todos_spans):
                        val_casa_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx - 1]).strip()
                        val_fora_str = driver.execute_script("return arguments[0].textContent;", todos_spans[idx + 1]).strip()
                        
                        match_c = re.search(r'\d+', val_casa_str)
                        match_f = re.search(r'\d+', val_fora_str)
                        
                        chutes_casa = int(match_c.group()) if match_c else 0
                        chutes_fora = int(match_f.group()) if match_f else 0
                        break
    except Exception as e:
        print(f"  ⚠️ Erro ao raspar estatísticas do jogo {url_jogo}: {e}")
        
    return chutes_casa, chutes_fora

def rodar_teste_chutes_totais_com_urls():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    # URL base H2H simulando o confronto
    url_base_h2h = "https://www.flashscore.com.br/jogo/futebol/cuiaba-zVvjqDOo/fortaleza-42FbPIs2/h2h/total/"
    url_base_limpa = url_base_h2h.replace("/h2h/total", "").rstrip("/")

    rotas_alvo = [
        {"tipo": "MANDANTE", "url": formatar_rota_h2h(url_base_limpa, "casa"), "chave_array_chutes": "chutes_mandante_h2h"},
        {"tipo": "VISITANTE", "url": formatar_rota_h2h(url_base_limpa, "fora"), "chave_array_chutes": "chutes_visitante_h2h"}
    ]
    
    print("\n🚀 INICIANDO TESTE ISOLADO: FORTALEZA X CUIABÁ (LÓGICA PRINCIPAL)\n" + "="*80)
    
    stats = {
        "chutes_mandante_h2h": [],
        "chutes_visitante_h2h": []
    }

    try:
        for alvo in rotas_alvo:
            print(f"\n🔍 [LOG] Acessando URL {alvo['tipo']}: {alvo['url']}")
            driver.get(alvo["url"])
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row, [class*='h2h__row']")))
            time.sleep(1.0)
            
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
            print(f"      📊 [LOG] Encontradas {len(linhas_confrontos)} linhas H2H para {alvo['tipo']}.")
            
            links_jogos = []
            for linha in linhas_confrontos[:5]:
                href = linha.get_attribute("href")
                if not href:
                    try:
                        a_tag = linha.find_element(By.TAG_NAME, "a")
                        href = a_tag.get_attribute("href")
                    except Exception:
                        pass
                if href and href not in links_jogos:
                    links_jogos.append(href)

            for idx, url_jogo in enumerate(links_jogos[:5], start=1):
                url_jogo_base = url_jogo.split("?")[0].split("#")[0].strip("/")
                c_casa, c_fora = extrair_estatisticas_partida(driver, url_jogo)
                
                if alvo["tipo"] == "MANDANTE" and c_casa > 0:
                    stats["chutes_mandante_h2h"].append(c_casa)
                    print(f"   • Mandante [{idx}/5] ➔ Chutes (Casa): {c_casa}")
                elif alvo["tipo"] == "VISITANTE" and c_fora > 0:
                    stats["chutes_visitante_h2h"].append(c_fora)
                    print(f"   • Visitante [{idx}/5] ➔ Chutes (Fora): {c_fora}")

        # Cálculo Final das Médias
        c_h2h = stats.get("chutes_mandante_h2h", [])
        v_h2h = stats.get("chutes_visitante_h2h", [])
        
        media_m = round(sum(c_h2h) / len(c_h2h), 2) if len(c_h2h) > 0 else 0.0
        media_v = round(sum(v_h2h) / len(v_h2h), 2) if len(v_h2h) > 0 else 0.0

        stats_teste = {
            "mandante_media_chutes_casa": media_m,
            "visitante_media_chutes_fora": media_v
        }

        resultado_mercados = verificar_chutes_totais(stats_teste)
        
        print("\n" + "="*80)
        print("3. RESULTADO DA MÉDIA DE CHUTES TOTAIS:")
        print(f"   • Média Calculada Mandante (Casa): {media_m} (Baseado em {len(c_h2h)} jogos)")
        print(f"   • Média Calculada Visitante (Fora): {media_v} (Baseado em {len(v_h2h)} jogos)")
        
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
                        
