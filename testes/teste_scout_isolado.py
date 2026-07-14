#testes/teste_scout_isolado.py
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    """Navega na aba específica (finalizacoes ou ataque) e extrai o scout correspondente."""
    # Monta a URL direta para a aba desejada
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.5) # Tempo para renderização da tabela
        
        # Define os termos de busca no cabeçalho baseados no mercado
        termos_busca = ["ALVO", "TARGET", "NO GOL"] if mercado == "finalizacoes" else ["SOFRIDAS", "SUFFERED", "FALTAS SOF"]
        
        # Identifica dinamicamente o índice da coluna
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in termos_busca) and not any(x in txt for x in ["XG", "XGOT", "COMETIDAS", "FOULS"]):
                indice_alvo = idx
                break
        
        # Se não achar dinamicamente, usa os índices padrão do Flashscore
        if indice_alvo == -1:
            indice_alvo = 5 if mercado == "finalizacoes" else 4

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
                    qtd_scout = int(valor_txt) if valor_txt.isdigit() else 0
                    
                    if nome_jogador not in acumulador_scouts:
                        acumulador_scouts[nome_jogador] = {
                            "time": time_real, 
                            "chutes_total": 0, "chutes_jogos": 0,
                            "faltas_total": 0, "faltas_jogos": 0
                        }
                    
                    if mercado == "finalizacoes":
                        acumulador_scouts[nome_jogador]["chutes_total"] += qtd_scout
                        acumulador_scouts[nome_jogador]["chutes_jogos"] += 1
                    else:
                        acumulador_scouts[nome_jogador]["faltas_total"] += qtd_scout
                        acumulador_scouts[nome_jogador]["faltas_jogos"] += 1
            except:
                continue
    except Exception as e:
        print(f"  ⚠️ Erro ao processar aba {mercado}: {e}")

def rodar_teste_completo_multi_mercado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    url_h2h_mae = "https://www.flashscore.com.br/jogo/futebol/espanha-bLyo6mco/franca-QkGeVG1n/h2h/total/"
    
    print("\n🚀 INICIANDO TESTE MULTI-MERCADO H2H: CHUTES NO GOL E FALTAS SOFRIDAS\n" + "="*80)
    print(f"🔗 Acessando H2H do confronto: {url_h2h_mae}")
    
    dicionario_escudos = {}
    links_jogos_historico = set()
    acumulador_scouts = {}

    try:
        driver.get(url_h2h_mae)
        time.sleep(4.0)
        
        blocos_h2h = driver.find_elements(By.CSS_SELECTOR, ".h2h__section, [class*='h2h__section']")
        for bloco in blocos_h2h:
            linhas_jogos = bloco.find_elements(By.CSS_SELECTOR, "a.h2h__row, [class*='h2h__row']")
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
            
        lista_final_links = list(links_jogos_historico)[:10]
        print(f"\n🔗 Total de jogos únicos para varrer (máximo 10): {len(lista_final_links)}")
        print("-" * 80)

        # Varre cada um dos jogos coletados executando os dois mercados por jogo
        for idx, url_jogo in enumerate(lista_final_links, start=1):
            print(f"实用 Processando jogo [{idx}/{len(lista_final_links)}]")
            
            if "?mid=" in url_jogo:
                parts = url_jogo.split("?mid=")
                url_base = parts[0].rstrip('/')
                mid_param = parts[1]
            else:
                url_base = url_jogo.split("/#")[0].rstrip('/')
                mid_param = ""

            # Extrai mercado 1: Chutes no Alvo
            extrair_scouts_por_aba(driver, url_base, mid_param, "finalizacoes", dicionario_escudos, acumulador_scouts)
            # Extrai mercado 2: Faltas Sofridas
            extrair_scouts_por_aba(driver, url_base, mid_param, "ataque", dicionario_escudos, acumulador_scouts)
            print("-" * 60)
            
        # Processamento de Médias e Filtro Final
        print("\n" + "="*80)
        print("📊 PROCESSAMENTO FINAL DAS MÉDIAS (REQUISITO: MÉDIA >= 1.0)")
        print("="*80)
        
        NOME_MANDANTE_REF = "AMÉRICA-MG"
        NOME_VISITANTE_REF = "LONDRINA"

        melhores = {
            NOME_MANDANTE_REF:  {"chutes": {"jogador": "Nenhum", "media": 0.0, "jogos": 0}, "faltas": {"jogador": "Nenhum", "media": 0.0, "jogos": 0}},
            NOME_VISITANTE_REF: {"chutes": {"jogador": "Nenhum", "media": 0.0, "jogos": 0}, "faltas": {"jogador": "Nenhum", "media": 0.0, "jogos": 0}}
        }

        for jogador, dados in acumulador_scouts.items():
            # Define a qual polo pertence o time detectado
            polo = None
            if NOME_MANDANTE_REF in dados["time"]: polo = NOME_MANDANTE_REF
            elif NOME_VISITANTE_REF in dados["time"]: polo = NOME_VISITANTE_REF
            
            if polo:
                # Média Chutes
                if dados["chutes_jogos"] > 0:
                    med_chutes = dados["chutes_total"] / dados["chutes_jogos"]
                    if med_chutes >= 1.0 and med_chutes > melhores[polo]["chutes"]["media"]:
                        melhores[polo]["chutes"] = {"jogador": jogador, "media": med_chutes, "jogos": dados["chutes_jogos"]}
                
                # Média Faltas Sofridas
                if dados["faltas_jogos"] > 0:
                    med_faltas = dados["faltas_total"] / dados["faltas_jogos"]
                    if med_faltas >= 1.0 and med_faltas > melhores[polo]["faltas"]["media"]:
                        melhores[polo]["faltas"] = {"jogador": jogador, "media": med_faltas, "jogos": dados["faltas_jogos"]}

        # Print do Log de Resultados Formatado
        for time_polo in [NOME_MANDANTE_REF, NOME_VISITANTE_REF]:
            print(f"\n🌟 MELHORES JOGADORES DO {time_polo}:")
            
            # Chutes
            if melhores[time_polo]["chutes"]["media"] >= 1.0:
                print(f"   🎯 Chutes no Alvo: {melhores[time_polo]['chutes']['jogador']} | Média: {melhores[time_polo]['chutes']['media']:.2f} ({melhores[time_polo]['chutes']['jogos']} jogos)")
            else:
                print("   ❌ Chutes no Alvo: Nenhum jogador atingiu a média mínima de 1.0.")
                
            # Faltas
            if melhores[time_polo]["faltas"]["media"] >= 1.0:
                print(f"   🤕 Faltas Sofridas: {melhores[time_polo]['faltas']['jogador']} | Média: {melhores[time_polo]['faltas']['media']:.2f} ({melhores[time_polo]['faltas']['jogos']} jogos)")
            else:
                print("   ❌ Faltas Sofridas: Nenhum jogador atingiu a média mínima de 1.0.")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo H2H: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE COMPLETO DE SCOUTS COMBINADOS")

if __name__ == "__main__":
    rodar_teste_completo_multi_mercado()
