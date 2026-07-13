import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_estatisticas_jogo(driver, url_jogo, dicionario_escudos, acumulador_scouts):
    """Navega até a sub-aba de finalizações corrigindo o posicionamento do parâmetro mid."""
    # 🎯 CORREÇÃO DA URL: Joga o ?mid= para o final correto da string
    if "?mid=" in url_jogo:
        parts = url_jogo.split("?mid=")
        url_base = parts[0].rstrip('/')
        mid_param = parts[1]
        url_finalizacoes = f"{url_base}/resumo/estatisticas-jogadores/finalizacoes/?mid={mid_param}"
    else:
        url_base = url_jogo.split("/#")[0].rstrip('/')
        url_finalizacoes = f"{url_base}/resumo/estatisticas-jogadores/finalizacoes/"

    print(f"  ➡️ Analisando: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0) # Tempo ideal para carregamento headless no Actions
        
        # Identifica o índice da coluna de chutes no alvo
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                break
        if indice_alvo == -1: 
            indice_alvo = 5

        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        
        for linha in linhas:
            try:
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "td[class*='isSticky'], td[class*='fitContent'], [data-testid='wcl-playerCell']")
                nome_element = celula_jogador.find_element(By.CSS_SELECTOR, "[class*='fp-playerName'], [class*='playerName']")
                nome_jogador = nome_element.text.strip()
                
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "div[class*='wcl-teamLogo'] img, div.wcl-teamLogo_sFhMr img")
                src_linha = img_logo.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                if time_real == "DESCONHECIDO":
                    continue
                
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_txt = celulas[indice_alvo].text.strip()
                    chutes = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    if nome_jogador not in acumulador_scouts:
                        acumulador_scouts[nome_jogador] = {"time": time_real, "total_chutes": 0, "jogos": 0}
                    
                    acumulador_scouts[nome_jogador]["total_chutes"] += chutes
                    acumulador_scouts[nome_jogador]["jogos"] += 1
            except:
                continue
    except Exception as e:
        print(f"  ⚠️ Erro ao processar este jogo: {e}")

def rodar_teste_completo_h2h():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    url_h2h_mae = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/londrina-pr-xdhbBEVA/h2h/total/"
    
    print("\n🚀 INICIANDO TESTE COMPLETO H2H CORRIGIDO: MÉDIA DE CHUTES NO ALVO\n" + "="*80)
    print(f"🔗 Acessando H2H do confronto: {url_h2h_mae}")
    
    dicionario_escudos = {}
    links_jogos_historico = set()
    acumulador_scouts = {}

    try:
        driver.get(url_h2h_mae)
        time.sleep(4.0)
        
        # Mapeamento dinâmico do Dicionário de Escudos direto nos blocos do H2H
        blocos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        
        for bloco in blocos_h2h:
            linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
            
            # 🎯 LIMITADOR CORRIGIDO: Coleta estritamente os 5 primeiros de cada bloco
            for linha_jogo in linhas_jogos[:5]:
                href = linha_jogo.get_attribute("href")
                if href:
                    links_jogos_historico.add(href)
                
                participantes = linha_jogo.find_elements(By.CSS_SELECTOR, "[class*='wcl-matchRow-participant'], .h2h__participant")
                for p in participantes:
                    try:
                        img_el = p.find_element(By.CSS_SELECTOR, "img")
                        src_img = img_el.get_attribute("src") or ""
                        nome_arquivo = src_img.split('/')[-1]
                        nome_time = p.text.strip().upper()
                        
                        if nome_arquivo and nome_time and nome_arquivo not in dicionario_escudos:
                            dicionario_escudos[nome_arquivo] = nome_time
                    except:
                        continue

        print(f"\n📦 Dicionário de Escudos mapeado dinamicamente via H2H ({len(dicionario_escudos)} times):")
        for png, time_nome in dicionario_escudos.items():
            print(f"    • {png} ➔ {time_nome}")
            
        lista_final_links = list(links_jogos_historico)
        print(f"\n🔗 Total de jogos únicos para varrer (máximo 10): {len(lista_final_links)}")
        print("-" * 80)

        # Varre cada um dos jogos coletados
        for idx, url_jogo in enumerate(lista_final_links, start=1):
            print(f"实用 Processando jogo [{idx}/{len(lista_final_links)}]")
            extrair_estatisticas_jogo(driver, url_jogo, dicionario_escudos, acumulador_scouts)
            
        # Processamento de Médias e Filtro
        print("\n" + "="*80)
        print("📊 PROCESSAMENTO FINAL DAS MÉDIAS")
        print("="*80)
        
        melhor_mandante = {"jogador": "Nenhum", "media": 0.0, "jogos": 0}
        melhor_visitante = {"jogador": "Nenhum", "media": 0.0, "jogos": 0}
        
        NOME_MANDANTE_REF = "AMÉRICA-MG"
        NOME_VISITANTE_REF = "LONDRINA"

        for jogador, dados in acumulador_scouts.items():
            if dados["jogos"] > 0:
                media = dados["total_chutes"] / dados["jogos"]
                
                if media >= 1.0:
                    if NOME_MANDANTE_REF in dados["time"]:
                        if media > melhor_mandante["media"]:
                            melhor_mandante = {"jogador": jogador, "media": media, "jogos": dados["jogos"]}
                    elif NOME_VISITANTE_REF in dados["time"]:
                        if media > melhor_visitante["media"]:
                            melhor_visitante = {"jogador": jogador, "media": media, "jogos": dados["jogos"]}

        print(f"\n🌟 MELHOR JOGADOR DO {NOME_MANDANTE_REF}:")
        if melhor_mandante["media"] >= 1.0:
            print(f"   👤 {melhor_mandante['jogador']} | 🎯 Média: {melhor_mandante['media']:.2f} chutes/jogo ({melhor_mandante['jogos']} partidas analisadas)")
        else:
            print("   ❌ Nenhum jogador atingiu a média mínima de 1.0 chutes no alvo.")

        print(f"\n🌟 MELHOR JOGADOR DO {NOME_VISITANTE_REF}:")
        if melhor_visitante["media"] >= 1.0:
            print(f"   👤 {melhor_visitante['jogador']} | 🎯 Média: {melhor_visitante['media']:.2f} chutes/jogo ({melhor_visitante['jogos']} partidas analisadas)")
        else:
            print("   ❌ Nenhum jogador atingiu a média mínima de 1.0 chutes no alvo.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo H2H: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE COMPLETO DE SCOUTS")

if __name__ == "__main__":
    rodar_teste_completo_h2h()
