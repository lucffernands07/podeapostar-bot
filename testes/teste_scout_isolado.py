import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_isolado():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Mockando as variáveis de ambiente que a função original exige
    url_jogo_completa = "https://www.flashscore.com.br/jogo/futebol/crb-QHa3bLrj/londrina-pr-xdhbBEVA"
    t1, t2 = "Londrina", "CRB"
    mandante_atual, visitante_atual = "Londrina", "CRB"
    
    stats = {
        "historico_chutes": {},
        "historico_faltas": {}
    }
    
    print("\n🚀 INICIANDO TESTE #37 (MÉTODO HISTÓRICO RECONSTRUTOR + LOG DE URL)\n" + "="*60)
    
    try:
        # Passo preliminar: Entrar na página principal para capturar os hashes dos escudos do topo
        print("[PASSO 0] Carregando topo para mapear hashes de imagem dos times...")
        driver.get(f"{url_jogo_completa}/resumo")
        time.sleep(4.0)
        
        hash_mandante_topo, hash_visitante_topo = "", ""
        try:
            img_m = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image, [class*='homeLogo'] img")
            hash_mandante_topo = img_m.get_attribute("src").split('/')[-1]
            img_v = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image, [class*='awayLogo'] img")
            hash_visitante_topo = img_v.get_attribute("src").split('/')[-1]
            print(f"   🛡️ Hashes detectados -> Mandante: {hash_mandante_topo} | Visitante: {hash_visitante_topo}")
        except Exception as e_hash:
            print(f"   ⚠️ Falha ao obter hashes das imagens do topo: {e_hash}")

        # 🎯 PASSO 2: Coleta de Chutes (Igual à sua lógica original)
        url_finalizacoes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
        print(f"\n🔗 [URL ALVO - PASSO 2]: Tentando raspar valores de FINALIZAÇÕES em: {url_finalizacoes}")
        driver.get(url_finalizacoes)
        
        try:
            driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(3.0)
            
            cabecalhos_fin = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
            indice_chutes = 5  
            for idx_th, th in enumerate(cabecalhos_fin):
                texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                if any(x in texto_th for x in ["ALVO", "TARGET"]) and not any(x in texto_th for x in ["XG", "XGOT"]):
                    indice_chutes = idx_th
                    break
            print(f"   ℹ️ Índice dinâmico da coluna de chutes no alvo: {indice_chutes}")
        
            linhas_dados_fin = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            print(f"   📊 Linhas brutas encontradas na tabela de finalizações: {len(linhas_dados_fin)}")
            
            for lambda_linha in linhas_dados_fin:
                try:
                    try:
                        nome_element = lambda_linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN, [class*='playerName'], [data-testid='wcl-playerCell']")
                    except: continue
                        
                    nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                    if not nome_jogador or nome_jogador == "TODOS": continue
                    
                    try:
                        img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='teamLogo'] img, [class*='wcl-teamLogo'] img")
                        hash_linha = img_linha.get_attribute("src").split('/')[-1]
                        
                        time_identificado = ""
                        if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                        elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                        else: continue 
                        
                        if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                            continue
                    except: continue

                    celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                    if len(celulas_valores) <= indice_chutes: continue
                    
                    val_chute = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_chutes]).strip()
                    chutes = int(re.search(r'\d+', val_chute).group()) if re.search(r'\d+', val_chute) else 0
        
                    if nome_jogador not in stats["historico_chutes"]: stats["historico_chutes"][nome_jogador] = []
                    stats["historico_chutes"][nome_jogador].append(chutes)
                    print(f"      👤 {nome_jogador:<20} ({time_identificado}) -> Chutes no Alvo: {chutes}")
                except: continue
        except Exception as e_passo2:
            print(f"   ⚠️ Erro ao processar dados de finalizações: {e_passo2}")

        # 🎯 PASSO 3: Coleta de Faltas Sofridas
        url_ataque = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
        print(f"\n🔗 [URL ALVO - PASSO 3]: Tentando raspar valores de FALTAS SOFRIDAS em: {url_ataque}")
        driver.get(url_ataque)
        
        try:
            driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(3.0)
            
            cabecalhos_atq = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell']")
            indice_faltas = 5  
            for idx_th, th in enumerate(cabecalhos_atq):
                texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                if any(x in texto_th for x in ["SOFRIDAS", "FALTAS SOFRIDAS", "FOULS SUFFERED", "FS"]):
                    indice_faltas = idx_th
                    break
            print(f"   ℹ️ Índice dinâmico da coluna de faltas: {indice_faltas}")
        
            linhas_dados_atq = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
            print(f"   📊 Linhas brutas encontradas na tabela de ataque: {len(linhas_dados_atq)}")
            
            for lambda_linha in linhas_dados_atq:
                try:
                    try:
                        nome_element = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], .fp-playerName_E6lgN")
                    except: continue
                        
                    nome_jogador = driver.execute_script("return arguments[0].textContent;", nome_element).strip()
                    if not nome_jogador or nome_jogador == "TODOS": continue
                    
                    try:
                        img_linha = lambda_linha.find_element(By.CSS_SELECTOR, "[class*='teamLogo'] img, [class*='wcl-teamLogo'] img")
                        hash_linha = img_linha.get_attribute("src").split('/')[-1]
                        
                        time_identificado = ""
                        if hash_linha == hash_mandante_topo: time_identificado = mandante_atual
                        elif hash_linha == hash_visitante_topo: time_identificado = visitante_atual
                        else: continue 
                        
                        if not (t1.upper() in time_identificado.upper() or t2.upper() in time_identificado.upper()):
                            continue
                    except: continue

                    celulas_valores = lambda_linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell']")
                    if len(celulas_valores) <= indice_faltas: continue
                    
                    val_falta = driver.execute_script("return arguments[0].textContent;", celulas_valores[indice_faltas]).strip()
                    faltas_sof = int(re.search(r'\d+', val_falta).group()) if re.search(r'\d+', val_falta) else 0
        
                    if nome_jogador not in stats["historico_faltas"]: stats["historico_faltas"][nome_jogador] = []
                    stats["historico_faltas"][nome_jogador].append(faltas_sof)
                    print(f"      👤 {nome_jogador:<20} ({time_identificado}) -> Faltas Sofridas: {faltas_sof}")
                except: continue
        except Exception as e_passo3:
            print(f"   ⚠️ Erro ao processar dados de faltas sofridas: {e_passo3}")

    except Exception as e:
        print(f"\n❌ Erro Crítico Executivo: {e}")
    finally:
        driver.quit()
        print("\n" + "="*60 + "\n🏁 FIM DO TESTE #37")

if __name__ == "__main__":
    rodar_teste_isolado()
                        
