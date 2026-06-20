import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Garante que o Python encontre os módulos da pasta raiz no GitHub Actions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

def testar_cartoes_pela_logica_main():
    driver = configurar_driver()
    wait = WebDriverWait(driver, 15)
    
    # URL do confronto base (H2H)
    url_inicial = "https://www.flashscore.com.br/jogo/futebol/escocia-fZRU25WH/marrocos-IDKYO3R8/h2h/total/"
    
    print("\n" + "="*70)
    print("🚀 INICIANDO ANÁLISE DUPLA H2H (MANDANTE E VISITANTE) FILTRADA POR IMAGEM")
    print("="*70 + "\n")
    
    # Dicionários separados por seleção alvo -> { Nome: [jogo1, jogo2, jogo3, jogo4, jogo5, jogo6] }
    historico_escocia_am = {}
    historico_escocia_vm = {}
    historico_marrocos_am = {}
    historico_marrocos_vm = {}
    
    # Configuração de varredura: Seção 1 (Mandante - Escócia) e Seção 2 (Visitante - Marrocos)
    secoes_alvo = [
        {"nome_time_base": "Escócia", "secao": 1},
        {"nome_time_base": "Marrocos", "secao": 2}
    ]
    
    # Índice global para controlar a posição do jogo na lista de históricos (0 a 5)
    jogo_global_index = 0

    try:
        print(f"1. URL DO CONFRONTO BASE (H2H):\n👉 {url_inicial}\n")
        
        for alvo in secoes_alvo:
            time_base = alvo["nome_time_base"]
            print(f"\n📋 COLETANDO 3 JOGOS DO HISTÓRICO DO(A): {time_base.upper()}")
            print("-" * 55)
            
            driver.get(url_inicial)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
            
            selector_linhas = f".h2h__section:nth-child({alvo['secao']}) .h2h__row"
            linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
            
            if len(linhas_confrontos) < 3:
                print(f"⚠️ Partidas insuficientes na seção {alvo['secao']} para processar 3 jogos.")
                continue

            quantidade_jogos = 3
            urls_jogos_alvo = []

            # Mapeia os confrontos antes de navegar
            for i in range(quantidade_jogos):
                try:
                    partes_texto = linhas_confrontos[i].text.split('\n')
                    nome_confronto = f"{partes_texto[2].strip()} x {partes_texto[3].strip()}"
                except:
                    nome_confronto = f"Jogo {i+1}"
                urls_jogos_alvo.append(nome_confronto)

            # --- LOOP PARA PROCESSAR OS JOGOS DA SEÇÃO ---
            for jogo_index in range(quantidade_jogos):
                print(f"🔄 Redirecionando para o Jogo {jogo_index + 1}: {urls_jogos_alvo[jogo_index]}...")
                
                # CORRIGIDO: alterado de juego_index para jogo_index
                if jogo_index > 0 or jogo_global_index > 0:
                    driver.get(url_inicial)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h2h__row")))
                    linhas_confrontos = driver.find_elements(By.CSS_SELECTOR, selector_linhas)
                
                elemento_alvo = linhas_confrontos[jogo_index]
                
                # Guarda quem é mandante e visitante do jogo atual por texto
                try:
                    partes_texto = elemento_alvo.text.split('\n')
                    mandante_atual = partes_texto[2].strip()
                    visitante_atual = partes_texto[3].strip()
                except:
                    mandante_atual, visitante_atual = "", ""

                url_anterior = driver.current_url
                driver.execute_script("arguments[0].click();", elemento_alvo)
                
                try:
                    WebDriverWait(driver, 7).until(lambda d: d.current_url != url_anterior)
                except:
                    pass
                    
                time.sleep(3)
                url_jogo_completa = driver.current_url.split("?")[0].strip("/")
                print(f"👉 URL DO CONFRONTO ATUAL: {url_jogo_completa}")

                # 📸 TRATAMENTO HISTÓRICO DA IMAGEM
                hash_mandante_topo = ""
                hash_visitante_topo = ""
                try:
                    img_m = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__homeLogo img.participant__image")
                    hash_mandante_topo = img_m.get_attribute("src").split('/')[-1]
                    
                    img_v = driver.find_element(By.CSS_SELECTOR, ".fixedHeaderDuel__awayLogo img.participant__image")
                    hash_visitante_topo = img_v.get_attribute("src").split('/')[-1]
                except Exception as e:
                    print(f"  ⚠️ Não foi possível ler as imagens dos escudos no topo: {e}")

                # --- RASPAGEM DA ABA: GERAIS ---
                url_gerais = f"{url_jogo_completa}/resumo/estatisticas-jogadores/gerais/"
                driver.get(url_gerais)
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='wcl-playerCell'], .fp-playerName_E6lgN")))
                    time.sleep(3)
                    
                    cabecalhos = driver.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-tableHeadCell'], .wcl-sortingButton_isgjY, th")
                    indice_amarelos = -1
                    indice_vermelhos = -1
                    
                    for idx, th in enumerate(cabecalhos):
                        texto_th = driver.execute_script("return arguments[0].textContent;", th).strip().upper()
                        alias = str(th.get_attribute("data-analytics-alias")).upper()
                        
                        if "AMARELO" in texto_th or alias == "YELLOW_CARDS" or texto_th == "CA":
                            indice_amarelos = idx
                        if "VERMELHO" in texto_th or alias == "RED_CARDS" or texto_th == "CV":
                            indice_vermelhos = idx
                    
                    linhas_dados = driver.find_elements(By.CSS_SELECTOR, "tr, .wcl-table__row_")
                    if len(linhas_dados) <= 1:
                        linhas_dados = driver.find_elements(By.CSS_SELECTOR, "div.wcl-table__body_ > div, [class*='tableRow']")
                        
                    for linha in linhas_dados:
                        try:
                            # 1. Extrai o nome do jogador
                            nome_jogador = driver.execute_script("return arguments[0].textContent;", linha.find_element(By.CSS_SELECTOR, ".fp-playerName_E6lgN")).strip()
                            if not nome_jogador or nome_jogador == "TODOS" or "JOGADOR" in nome_jogador.upper():
                                continue
                            
                            # 2. SEPARAÇÃO POR FILTRO DE IMAGEM
                            try:
                                img_linha = linha.find_element(By.CSS_SELECTOR, "[class*='wcl-teamLogo'] img")
                                hash_linha = img_linha.get_attribute("src").split('/')[-1]
                            except:
                                hash_linha = ""

                            if hash_linha and hash_linha == hash_mandante_topo:
                                time_identificado = mandante_atual
                            elif hash_linha and hash_linha == hash_visitante_topo:
                                time_identificado = visitante_atual
                            else:
                                time_identificado = "OUTRO"

                            if "ESCÓCIA" in time_identificado.upper() or "SCOTLAND" in time_identificado.upper():
                                dicionario_am = historico_escocia_am
                                dicionario_vm = historico_escocia_vm
                            elif "MARROCOS" in time_identificado.upper() or "MOROCCO" in time_identificado.upper():
                                dicionario_am = historico_marrocos_am
                                dicionario_vm = historico_marrocos_vm
                            else:
                                continue

                            # 3. Extração dos valores numéricos
                            celulas_valores = linha.find_elements(By.CSS_SELECTOR, "[data-testid='wcl-scores-simple-text-01'], td, .wcl-table__bodyCell_")
                            if not celulas_valores:
                                continue
                                
                            if indice_amarelos != -1 and indice_vermelhos != -1 and len(celulas_valores) > max(indice_amarelos, indice_vermelhos):
                                idx_am = indice_amarelos
                                idx_vm = indice_vermelhos
                            else:
                                idx_am = len(celulas_valores) - 3 if len(celulas_valores) >= 3 else 0
                                idx_vm = len(celulas_valores) - 2 if len(celulas_valores) >= 2 else 0

                            val_amarelo = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_am]).strip()
                            val_vermelho = driver.execute_script("return arguments[0].textContent;", celulas_valores[idx_vm]).strip()
                            
                            amarelos = 0 if val_amarelo in ["-", ""] or not val_amarelo.replace(r'\D', '').isdigit() else int(re.sub(r'\D', '', val_amarelo))
                            vermelhos = 0 if val_vermelho in ["-", ""] or not val_vermelho.replace(r'\D', '').isdigit() else int(re.sub(r'\D', '', val_vermelho))
                            
                            if nome_jogador not in dicionario_am:
                                dicionario_am[nome_jogador] = []
                            while len(dicionario_am[nome_jogador]) < jogo_global_index:
                                dicionario_am[nome_jogador].append(0)
                            dicionario_am[nome_jogador].append(amarelos)
                            
                            if nome_jogador not in dicionario_vm:
                                dicionario_vm[nome_jogador] = []
                            while len(dicionario_vm[nome_jogador]) < jogo_global_index:
                                dicionario_vm[nome_jogador].append(0)
                            dicionario_vm[nome_jogador].append(vermelhos)

                        except:
                            continue
                except Exception as e:
                    print(f"  ⚠️ Sem dados de Cartões Gerais para este jogo: {e}\n")
                
                print(f"✅ Jogo {jogo_index + 1} da seção processado com sucesso.\n" + "-"*40)
                jogo_global_index += 1

       # --- PROCESSAMENTO DOS CONSOLIDADOS E MÉDIAS POR SELEÇÃO ---
        print("\n" + "="*70)
        print(f"📊 RELATÓRIO FINAL DE MÉDIAS DOS JOGOS MAPEADOS")
        print("="*70)
        
        selecoes_prints = [
            {"nome": "ESCÓCIA", "dict_am": historico_escocia_am, "dict_vm": historico_escocia_vm, "inicio_idx": 0, "fim_idx": 3},
            {"nome": "MARROCOS", "dict_am": historico_marrocos_am, "dict_vm": historico_marrocos_vm, "inicio_idx": 3, "fim_idx": 6}
        ]
        
        jogos_por_time = 3
        total_cartoes_escocia = 0
        total_cartoes_marrocos = 0
        
        for sel in selecoes_prints:
            print(f"\n🟩 SELEÇÃO DA {sel['nome']}:")
            print("-" * 55)
            
            if not sel["dict_am"]:
                print("  Nenhum jogador recebeu cartões nos jogos listados.")
                continue
                
            for jogador, lista_amarelos in sel["dict_am"].items():
                lista_vermelhos = sel["dict_vm"].get(jogador, [])
                
                while len(lista_amarelos) < jogo_global_index:
                    lista_amarelos.append(0)
                while len(lista_vermelhos) < jogo_global_index:
                    lista_vermelhos.append(0)
                    
                lista_combinada = [lista_amarelos[x] + lista_vermelhos[x] for x in range(jogo_global_index)]
                
                # Separa os jogos reais do time para a média individual correta
                jogos_reais_do_time = lista_combinada[sel["inicio_idx"]:sel["fim_idx"]]
                amarelos_reais = lista_amarelos[sel["inicio_idx"]:sel["fim_idx"]]
                vermelhos_reais = lista_vermelhos[sel["inicio_idx"]:sel["fim_idx"]]
                
                # Acumula para a soma coletiva do time
                soma_jogador = sum(jogos_reais_do_time)
                if sel["nome"] == "ESCÓCIA":
                    total_cartoes_escocia += soma_jogador
                else:
                    total_cartoes_marrocos += soma_jogador
                
                media_real = soma_jogador / jogos_por_time
                
                if soma_jogador > 0:
                    print(f"  👤 {jogador.ljust(25)} ➔ Média Real: {media_real:.2f} cartões/jogo {jogos_reais_do_time} (Am: {amarelos_reais} | Vm: {vermelhos_reais})")

        # --- LOG COMPLEMENTAR: MÉTRICA COLETIVA DO CONFRONTO ---
        total_geral_confronto = total_cartoes_escocia + total_cartoes_marrocos
        media_geral_confronto = total_geral_confronto / jogo_global_index if jogo_global_index > 0 else 0
        
        print("\n" + "="*70)
        print("📈 SUMÁRIO COLETIVO DO CONFRONTO (BUSINESS LOGIC)")
        print("="*70)
        print(f"🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia nos 3 jogos: {total_cartoes_escocia} cartões")
        print(f"🇲🇦 Marrocos nos 3 jogos: {total_cartoes_marrocos} cartões")
        print(f"🧮 Total Geral Analisado: {total_geral_confronto} cartões em {jogo_global_index} jogos")
        print(f"📊 Média Final do Confronto: {media_geral_confronto:.2f} cartões por jogo")

    except Exception as e:
        print(f"\n❌ Erro crítico no fluxo de médias: {e}")
    finally:
        driver.quit()
        print("\n" + "="*70)
        print("🏁 Análise inteligente de cartões finalizada com sucesso.")
        print("="*70)
        
if __name__ == "__main__":
    testar_cartoes_pela_logica_main()
    
