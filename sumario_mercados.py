import re
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false") # Agiliza o carregamento ignorando imagens
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def interpretar_texto(texto_sumario):
    """
    Processa o texto descritivo do sumário e ativa os mercados com base em palavras-chave.
    """
    texto_lower = texto_sumario.lower()
    
    diagnostico = {
        "vitoria": {"possivel": False, "motivo": ""},
        "dupla_chance": {"possivel": False, "motivo": ""},
        "quantidade_gols": {"possivel": False, "motivo": ""},
        "btts": {"possivel": False, "motivo": ""},
        "chutes_no_gol_jogador": {"possivel": False, "jogadores": []},
        "quantidade_cartoes": {"possivel": False, "motivo": ""}
    }

    # 1. MERCADO: VITÓRIA
    if any(t in texto_lower for t in ["favorit", "franco favor", "dominar", "superioridade", "vencer confortavelmente"]):
        diagnostico["vitoria"]["possivel"] = True
        diagnostico["vitoria"]["motivo"] = "Texto indica favoritismo ou superioridade acentuada."

    # 2. MERCADO: DUPLA CHANCE
    if any(t in texto_lower for t in ["equilibrad", "confronto parelho", "tendência de empate", "equipes se equivalem", "jogo duro"]):
        diagnostico["dupla_chance"]["possivel"] = True
        diagnostico["dupla_chance"]["motivo"] = "Confronto equilibrado ou truncado; ideal para Dupla Chance protetiva."
    elif diagnostico["vitoria"]["possivel"]:
        diagnostico["dupla_chance"]["possivel"] = True
        diagnostico["dupla_chance"]["motivo"] = "Favorito mapeado; chance dupla de segurança a favor do time mais forte."

    # 3. MERCADO: QUANTIDADE DE GOLS
    if any(t in texto_lower for t in ["ataque avassalador", "goleada", "gols", "ofensiv", "placar elástico", "artilheiro"]):
        diagnostico["quantidade_gols"]["possivel"] = True
        diagnostico["quantidade_gols"]["motivo"] = "Análise indica alta presença ofensiva (Tendência de Over)."
    elif any(t in texto_lower for t in ["defesa sólida", "retranca", "jogo fechado", "poucos gols", "foco defensivo", "amarrado"]):
        diagnostico["quantidade_gols"]["possivel"] = True
        diagnostico["quantidade_gols"]["motivo"] = "Texto foca em consistência defensiva ou jogo travado (Tendência de Under)."

    # 4. MERCADO: BTTS (Ambos Marcam)
    if any(t in texto_lower for t in ["ambas marcam", "vulnerabilidade defensiva", "ambos os lados", "lá e cá", "troca de golpes", "vazada"]):
        diagnostico["btts"]["possivel"] = True
        diagnostico["btts"]["motivo"] = "Mencionou fragilidades em ambos os setores defensivos ou ritmo franco."

    # 5. MERCADO: CHUTES NO GOL DE JOGADOR
    estrelas_copa = ["messi", "ronaldo", "mbappé", "bellingham", "vinicius", "haaland", "kane", "griezmann", "lewandowski"]
    for estrela in estrelas_copa:
        if estrela in texto_lower:
            diagnostico["chutes_no_gol_jogador"]["possivel"] = True
            diagnostico["chutes_no_gol_jogador"]["jogadores"].append(estrela.capitalize())
            
    if any(t in texto_lower for t in ["inspirado", "finalizador", "chuta muito", "chutes", "finalizações"]):
        diagnostico["chutes_no_gol_jogador"]["possivel"] = True
        if not diagnostico["chutes_no_gol_jogador"]["jogadores"]:
            diagnostico["chutes_no_gol_jogador"]["jogadores"].append("Destaque Ofensivo Citado")

    # 6. MERCADO: QUANTIDADE DE CARTÕES
    if any(t in texto_lower for t in ["cartão", "cartões", "árbitro", "juiz", "faltoso", "clima tenso", "rivalidade", "truncado", "jogo duro", "disciplinar"]):
        diagnostico["quantidade_cartoes"]["possivel"] = True
        diagnostico["quantidade_cartoes"]["motivo"] = "Texto cita arbitragem rígida ou expectativa de jogo faltoso/nervoso."

    return diagnostico

def main():
    print("\n🤖 [INICIANDO SCRAPER COMPLETO DA COPA DO MUNDO]")
    driver = configurar_driver()
    wait = WebDriverWait(driver, 12)
    
    # 📌 URL Geral da Copa do Mundo no Flashscore para pegar os jogos do dia
    url_copa_do_mundo = "https://www.flashscore.com.br/futebol/mundo/campeonato-do-mundo/"
    
    try:
        print(f"🌍 Acessando o painel de jogos da competição...")
        driver.get(url_copa_do_mundo)
        time.sleep(5)
        
        # Coleta todos os blocos de jogos ativos ou agendados em exibição na tela
        elementos_jogos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        print(f"🔍 Encontrados {len(elementos_jogos)} jogos no painel principal.\n")
        
        jogos_mapeados = []
        
        # Primeiro passo: Extrai os metadados de identificação sem abrir abas novas para não perder o DOM
        for el in elementos_jogos:
            try:
                id_jogo = el.get_attribute('id').split('_')[-1]
                times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name']")
                t1 = times[0].text.strip()
                t2 = times[1].text.strip()
                
                jogos_mapeados.append({
                    "id": id_jogo,
                    "casa": t1,
                    "fora": t2,
                    "url": f"https://www.flashscore.com.br/jogo/{id_jogo}/"
                })
            except Exception:
                continue

        # Se a lista estiver vazia (por exemplo, em ambiente de teste local), injetamos o link de teste padrão
        if not jogos_mapeados:
            print("ℹ️ Nenhum jogo ativo encontrado na Home. Usando o jogo de teste (Argentina x Áustria)...")
            jogos_mapeados.append({
                "id": "f9OppQjp",
                "casa": "Argentina",
                "fora": "Áustria",
                "url": "https://www.flashscore.com.br/jogo/futebol/argentina-f9OppQjp/austria-naHiWdnt/"
            })

        # Segundo passo: Navega individualmente no sumário de cada confronto e gera os LOGS
        for jogo in jogos_mapeados:
            print("=" * 70)
            print(f"🏟️ CONFRONTO: {jogo['casa']} x {jogo['fora']}")
            print(f"🔗 URL: {jogo['url']}")
            print("-" * 70)
            
            # Abre o sumário em uma nova aba para processamento isolado
            driver.execute_script(f"window.open('{jogo['url']}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            
            try:
                # Captura o texto do Sumário escrito
                elemento_texto = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, ".previewShowMore, [class*='previewDescription'], [class*='previewText']"
                )))
                
                # Tenta expandir o texto se o botão "Mostrar pré-jogo detalhado" estiver presente
                try:
                    btn_mais = driver.find_element(By.CSS_SELECTOR, ".previewShowMore__button, [class*='showMore']")
                    driver.execute_script("arguments[0].click();", btn_mais)
                    time.sleep(0.5)
                except:
                    pass
                
                texto_sumario = driver.execute_script("return arguments[0].textContent;", elemento_texto).strip()
                print(f"📖 TEXTO EXTRAÍDO:\n\"{texto_sumario}\"\n")
                
                # Executa o Motor NLP de interpretação
                analise = interpretar_texto(texto_sumario)
                
                print("📊 DIAGNÓSTICO DE MERCADOS VIA LOG:")
                for mercado, dados in analise.items():
                    if dados["possivel"]:
                        print(f"  ✅ [{mercado.upper()}] - Ativado com sucesso!")
                        if "motivo" in dados and dados["motivo"]:
                            print(f"     ↳ Razão: {dados['motivo']}")
                        if "jogadores" in dados and dados["jogadores"]:
                            print(f"     ↳ Atletas Relacionados: {', '.join(dados['jogadores'])}")
                    else:
                        print(f"  ❌ [{mercado.upper()}] - Sem evidências textuais.")
                        
            except Exception as e:
                print(f"⚠️ Erro ao raspar o sumário deste jogo: {e}")
                
            # Fecha a aba da partida e retorna para o painel principal
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            print("=" * 70 + "\n")

    except Exception as e:
        print(f"🚨 Erro crítico na execução do Scraper: {e}")
    finally:
        driver.quit()
        print("🤖 [SCRAPER FINALIZADO]")

if __name__ == "__main__":
    main()
    
