import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def rodar_teste_finalizacoes():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    # URL do jogo histórico
    url_finalizacoes = "https://www.flashscore.com.br/jogo/futebol/america-mg-xUT0Bp8o/cuiaba-zVvjqDOo/resumo/estatisticas-jogadores/finalizacoes/?mid=QVKCjMJD"
    
    print("\n🔥 TESTE ISOLADO V6: MAIS RECENTE COMPARANDO PNG DIRETO\n" + "="*70)
    print(f"🔗 Acessando: {url_finalizacoes}")
    
    try:
        driver.get(url_finalizacoes)
        time.sleep(4.0)
        
        # 🟢 REFERÊNCIA DE HOJE: Simulando os arquivos salvos do confronto principal antes de abrir os históricos
        # Como visto no seu log, o robô já sabe esses dois valores perfeitamente:
        arquivo_mandante_hoje = "COoi5ag5-CWl52SGk.png"  # Cuiabá no histórico (ou América no principal)
        arquivo_visitante_hoje = "Eut0HLfM-nHqWQgSo.png" # América no histórico (ou Cuiabá no principal)
        
        print(f"📌 Imagens de Referência Salvas (Jogo Principal):")
        print(f"   🏠 Mandante Principal: {arquivo_mandante_hoje}")
        print(f"   🚀 Visitante Principal: {arquivo_visitante_hoje}\n")

        # 1️⃣ Localiza a coluna de "Finalizações no Alvo"
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "th, [data-testid='wcl-tableHeadCell'], .wcl-tableHeadCell_")
        indice_alvo = -1
        for idx, th in enumerate(cabecalhos):
            txt = th.text.strip().upper()
            if any(x in txt for x in ["ALVO", "TARGET", "NO GOL"]) and not any(x in txt for x in ["XG", "XGOT"]):
                indice_alvo = idx
                print(f"🎯 Coluna identificada no Índice [{idx}]")
                break
        if indice_alvo == -1: indice_alvo = 5

        # 2️⃣ Varre a tabela de jogadores
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr[class*='row'], tr, .wcl-table__row_, [data-testid='wcl-tableRow']")
        print(f"\n📊 Total de linhas brutas encontradas na tabela: {len(linhas)}")
        print("-" * 70)
        
        contagem_impressos = 0
        for linha in linhas:
            try:
                # Localiza o nome do jogador
                nome_element = linha.find_element(By.CSS_SELECTOR, "[class*='playerName'], [data-testid='wcl-playerCell'], [class^='fp-playerName_']")
                nome_jogador = nome_element.text.split('\n')[0].strip()
                if not nome_jogador or nome_jogador == "TODOS": 
                    continue
                
                # 🟢 CORREÇÃO DOS SELETORES: Busca a img especificamente dentro do container do logotipo do time 
                # Isso impede o robô de pegar por engano a foto do rosto do atleta
                img_linha = linha.find_element(By.CSS_SELECTOR, "div[class*='teamLogo'] img, [class*='wcl-teamLogo'] img, div[class*='assetContainer'] img")
                src_linha = img_linha.get_attribute("src") or ""
                arquivo_linha = src_linha.split('/')[-1] if src_linha else ""
                
                time_pertencente = "DESCONHECIDO"
                
                # Compara direto o arquivo coletado na linha com as referências que você já guardou antes
                if arquivo_linha and arquivo_linha == arquivo_mandante_hoje:
                    time_pertencente = "MANDANTE"
                elif arquivo_linha and arquivo_linha == arquivo_visitante_hoje:
                    time_pertencente = "VISITANTE"
                
                # Captura os scouts daquela linha
                celulas = linha.find_elements(By.CSS_SELECTOR, "td, [data-testid='wcl-tableBodyCell'], .wcl-tableBodyCell_")
                if len(celulas) > indice_alvo:
                    valor_chute_alvo = celulas[indice_alvo].text.strip()
                    print(f"👤 Jogador: {nome_jogador.ljust(22)} | 👥 Time: {time_pertencente.ljust(11)} | 🎯 Chutes no Alvo: {valor_chute_alvo}")
                    contagem_impressos += 1
            except:
                continue

        print("-" * 70)
        print(f"✅ Extração finalizada. Total de jogadores válidos printados: {contagem_impressos}")

    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
    finally:
        driver.quit()
        print("\n🏁 FIM DO TESTE ISOLADO")

if __name__ == "__main__":
    rodar_teste_finalizacoes()
