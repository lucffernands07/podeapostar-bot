import time
from selenium.webdriver.common.by import By

def extrair_scouts_por_aba(driver, url_base, mid_param, mercado, dicionario_escudos, acumulador_scouts):
    url_final = f"{url_base}/resumo/estatisticas-jogadores/{mercado}/?mid={mid_param}"
    print(f"  ➡️ Analisando {mercado.upper()}: {url_final}")
    
    try:
        driver.get(url_final)
        time.sleep(3.0)
        
        # Regra solicitada: 5 para faltas (ataque), 6 para chutes (finalizacoes)
        indice_alvo = 5 if mercado == "ataque" else 6
        
        linhas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableRow']")
        print(f"     📊 Linhas encontradas na tabela: {len(linhas)}")
        
        for linha in linhas:
            try:
                # Extração jogador e escudo
                celula_jogador = linha.find_element(By.CSS_SELECTOR, "[data-testid='wcl-playerCell']")
                nome_jogador = celula_jogador.text.strip()
                img_logo = celula_jogador.find_element(By.CSS_SELECTOR, "img")
                arquivo_linha = img_logo.get_attribute("src").split('/')[-1]
                time_real = dicionario_escudos.get(arquivo_linha, "DESCONHECIDO")
                
                # Extração valor
                celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableBodyCell']")
                valor_txt = celulas[indice_alvo].text.strip() if len(celulas) > indice_alvo else "0"
                qtd = int(valor_txt) if valor_txt.isdigit() else 0
                
                # LOG DE AUDITORIA: SEMPRE APARECE
                print(f"     👤 Jogador: {nome_jogador:20} | EscudoID: {arquivo_linha} | Time: {time_real} | Qtd: {qtd}")
                
                if time_real != "DESCONHECIDO" and qtd > 0:
                    if nome_jogador not in acumulador_scouts:
                        acumulador_scouts[nome_jogador] = {"time": time_real, "chutes": 0, "c_jogos": 0, "faltas": 0, "f_jogos": 0}
                    
                    if mercado == "finalizacoes":
                        acumulador_scouts[nome_jogador]["chutes"] += qtd
                        acumulador_scouts[nome_jogador]["c_jogos"] += 1
                    else:
                        acumulador_scouts[nome_jogador]["faltas"] += qtd
                        acumulador_scouts[nome_jogador]["f_jogos"] += 1
            except: continue
    except Exception as e:
        print(f"  ⚠️ Erro na extração da aba {mercado}: {e}")

def pegar_scouts_avancados(driver, dados_jogo, t1, t2):
    url_h2h_mae = dados_jogo.get("url_h2h_base")
    driver.get(url_h2h_mae)
    time.sleep(4.0)
    
    # Mapeamento
    dicionario_escudos = {}
    for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-matchRow-participant']"):
        try:
            img = c.find_element(By.CSS_SELECTOR, "img")
            nome = c.find_element(By.CSS_SELECTOR, "span[data-testid='wcl-scores-simple-text-01']").text.strip().upper()
            dicionario_escudos[img.get_attribute("src").split('/')[-1]] = nome
            print(f"    • {img.get_attribute('src').split('/')[-1]} ➔ {nome}")
        except: continue

    # Filtro de data: mantendo apenas 2025/2026
    elementos = driver.find_elements(By.CSS_SELECTOR, "a.h2h__row")
    links_historico = [l.get_attribute("href") for l in elementos if any(ano in l.text for ano in ["2025", "2026"])]
    print(f"\n🔗 Total de jogos únicos (filtrados): {len(links_historico)}")

    acumulador = {}
    for url_jogo in links_historico:
        mid = url_jogo.split("?mid=")[1] if "?mid=" in url_jogo else ""
        url_base = url_jogo.split("/?")[0].rstrip('/')
        
        # Chamadas de extração (que geram as logs de jogador)
        extrair_scouts_por_aba(driver, url_base, mid, "finalizacoes", dicionario_escudos, acumulador)
        extrair_scouts_por_aba(driver, url_base, mid, "ataque", dicionario_escudos, acumulador)

    # Resumo final
    print("\n" + "="*80)
    print("📊 RESULTADOS FINAIS (MÉDIA >= 1.0):")
    for time_alvo in [t1, t2]:
        print(f"\n{time_alvo.upper()}:")
        jogadores = {k: v for k, v in acumulador.items() if v['time'] == time_alvo.upper()}
        for nome, d in jogadores.items():
            m_c = d['chutes'] / d['c_jogos'] if d['c_jogos'] > 0 else 0
            m_f = d['faltas'] / d['f_jogos'] if d['f_jogos'] > 0 else 0
            
            if m_c >= 1.0: print(f"  Chutes no gol: {nome} média {m_c:.1f}")
            if m_f >= 1.0: print(f"  Faltas sofridas: {nome} média {m_f:.1f}")
    
    return dados_jogo
    
