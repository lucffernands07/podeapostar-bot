import os
import sys
import time
import json

# 🔥 PRIMEIRO: Garante que o Python encontre os módulos da pasta raiz no GitHub Actions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora as importações normais do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importa a função de análise real E a lista branca do seu arquivo mercados/jogadores.py
from mercados.jogadores import verificar_destaques_jogadores, LIGAS_ELITE_JOGADORES

CAMINHO_JSON_TESTE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jogos_hoje.json'))

def criar_json_ficticio_para_teste():
    """Cria um arquivo jogos_hoje.json temporário apenas para o ambiente de teste"""
    dados_teste = [
        {
            "time_casa": "Escócia",
            "time_fora": "Marrocos",
            "liga": "Mundo - Copa do Mundo",
            "url_flashscore": "https://www.flashscore.com.br/jogo/futebol/escocia-fZRU25WH/marrocos-IDKYO3R8/h2h/total/"
        }
        # Se quiser testar o comportamento com mais jogos no JSON, adicione aqui:
        # ,{
        #     "time_casa": "Time A",
        #     "time_fora": "Time B",
        #     "liga": "Brasileirão Série B",
        #     "url_flashscore": "https://www.flashscore.com.br/link-do-jogo/h2h/total/"
        # }
    ]
    
    with open(CAMINHO_JSON_TESTE, 'w', encoding='utf-8') as f:
        json.dump(dados_teste, f, ensure_ascii=False, indent=4)
    print(f"✅ Arquivo temporário 'jogos_hoje.json' criado com sucesso para o teste.")

def carregar_jogos_do_dia():
    """Busca os confrontos listados no json gerado para o teste"""
    if not os.path.exists(CAMINHO_JSON_TESTE):
        print(f"⚠️ Arquivo 'jogos_hoje.json' não encontrado em: {CAMINHO_JSON_TESTE}")
        return []
    
    try:
        with open(CAMINHO_JSON_TESTE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler jogos_hoje.json: {e}")
        return []

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def rodar_teste_simulado_main():
    # 1. Cria o ambiente gerando o arquivo JSON que a lógica precisa encontrar
    criar_json_ficticio_para_teste()

    # 2. Carrega os jogos do arquivo gerado
    jogos = carregar_jogos_do_dia()
    if not jogos:
        print("❌ Nenhum jogo disponível para rodar o teste de validação.")
        return

    # 3. Filtra dinamicamente usando a lista branca real do mercados/jogadores.py
    jogos_validos = [j for j in jogos if j.get('liga', '').strip() in LIGAS_ELITE_JOGADORES and j.get('url_flashscore')]
    
    print("\n" + "="*60)
    print(f"🚀 COLETANDO E ENVIANDO {len(jogos_validos)} JOGOS DA LISTA BRANCA PARA O JOGADORES.PY")
    print("="*60)

    if not jogos_validos:
        print("⏩ [TESTE] Nenhum dos jogos simulados no JSON pertence às ligas Elite de Jogadores.")
        return

    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    quantidade_jogos = 3

    for idx_jogo, jogo in enumerate(jogos_validos):
        t1 = jogo.get('time_casa', 'Mandante')
        t2 = jogo.get('time_fora', 'Visitante')
        liga = jogo.get('liga', 'Liga Desconhecida').strip()
        url_inicial = jogo.get('url_flashscore')

        if not url_inicial.endswith('/h2h/total/') and not url_inicial.endswith('/h2h/'):
            url_inicial = url_inicial.strip('/') + '/h2h/total/'

        print(f"\n🌍 [{idx_jogo + 1}/{len(jogos_validos)}] Raspando: {t1} x {t2} ({liga})")
        
        historico_chutes = {}
        historico_faltas = {}

        try:
            driver.get(url_inicial)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row") or driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
            
            loops_reais = min(quantidade_jogos, len(linhas_confrontos))

            for jogo_index in range(loops_reais):
                try:
                    if jogo_index > 0:
                        driver.get(url_inicial)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                        linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, ".h2h__section:nth-child(1) .h2h__row") or driver.find_elements(By.CSS_SELECTOR, ".h2h__row")
                    
                    if len(linhas_confrontos) <= jogo_index: continue
                    elemento_alvo = linhas_confrontos[jogo_index]
                    url_anterior = driver.current_url
                    driver.execute_script("arguments[0].click();", elemento_alvo)
                    
                    try:
                        WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                    except: pass
                        
                    time.sleep(2)
                    url_jogo_completa = driver.current_url.split("?")[0].strip("/")

                    # --- RASPAGEM FINALIZAÇÕES ---
                    url_chutes = f"{url_jogo_completa}/resumo/estatisticas-jogadores/finalizacoes/"
                    driver.get(url_chutes)
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                        indice_chutes = -1
                        for idx, th in enumerate(cabecalhos):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            alias = str(th.get_attribute("data-analytics-alias")).upper()
                            if "ALVO" in texto_th or alias == "SHOTS_ON_TARGET":
                                indice_chutes = idx
                                break
                        
                        if indice_chutes != -1:
                            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_") or driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                            for linha in linhas_dados:
                                try:
                                    nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper(): continue
                                    celulas = Pioneer = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                                    if len(celulas) > indice_chutes:
                                        val = driver.execute_script("return arguments[0].textContent;", celulas[indice_chutes]).strip()
                                        qtd = 0 if val in ["-", ""] else int(val)
                                        if nome_jogador not in historico_chutes: historico_chutes[nome_jogador] = []
                                        while len(historico_chutes[nome_jogador]) < jogo_index: historico_chutes[nome_jogador].append(0)
                                        historico_chutes[nome_jogador].append(qtd)
                                except: continue
                    except: pass

                    # --- RASPAGEM FALTAS SOFRIDAS ---
                    url_faltas = f"{url_jogo_completa}/resumo/estatisticas-jogadores/ataque/"
                    driver.get(url_faltas)
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .fp-playerName_E6lgN")))
                        cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                        indice_faltas = -1
                        for idx, th in enumerate(cabecalhos):
                            texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                            alias = str(th.get_attribute("data-analytics-alias")).upper()
                            if alias == "FOULS_SUFFERED" or "SOFRIDAS" in texto_th:
                                indice_faltas = idx
                                break
                        
                        if indice_faltas != -1:
                            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_") or driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                            for linha in linhas_dados:
                                try:
                                    nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                                    if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper(): continue
                                    celulas = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                                    if len(celulas) > indice_faltas:
                                        val = driver.execute_script("return arguments[0].textContent;", celulas[indice_faltas]).strip()
                                        qtd = 0 if val in ["-", ""] or "%" in val or "/" in val else int(val)
                                        if nome_jogador not in historico_faltas: historico_faltas[nome_jogador] = []
                                        while len(historico_faltas[nome_jogador]) < jogo_index: historico_faltas[nome_jogador].append(0)
                                        historico_faltas[nome_jogador].append(qtd)
                                except: continue
                    except: pass
                except: continue

            # 🔥 ENVIA OS DADOS RASPADOS PARA O SEU JOGADORES.PY COMPATÍVEL COM A LIGA DO JSON
            resultados_analise = verificar_destaques_jogadores(
                historico_chutes=historico_chutes,
                historico_faltas=historico_faltas,
                quantidade_jogos=quantidade_jogos,
                nome_liga=liga
            )

            if resultados_analise:
                print(f" 🟢 [APROVADO]:")
                for res in resultados_analise:
                    print(f"    🔶 {res['texto']}")
            else:
                print(f" 🔴 [NEGADO/VAZIO] Ninguém atingiu os critérios.")

        except Exception as e:
            print(f"❌ Erro no confronto: {e}")

    driver.quit()
    
    # 4. Limpa o arquivo temporário criado para deixar o ambiente limpo
    if os.path.exists(CAMINHO_JSON_TESTE):
        os.remove(CAMINHO_JSON_TESTE)

if __name__ == "__main__":
    rodar_teste_simulado_main()
