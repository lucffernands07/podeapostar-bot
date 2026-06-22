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
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def interpretar_texto(texto_sumario):
    texto_lower = texto_sumario.lower()
    
    diagnostico = {
        "vitoria": {"possivel": False, "motivo": ""},
        "dupla_chance": {"possivel": False, "motivo": ""},
        "gols_over_1_5": {"possivel": False, "motivo": ""},
        "gols_over_2_5": {"possivel": False, "motivo": ""},
        "gols_under_4_5": {"possivel": False, "motivo": ""},
        "btts": {"possivel": False, "motivo": ""},
        "chutes_no_gol_jogador": {"possivel": False, "motivo": "", "jogadores": []},
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

    # 3. MERCADOS DE GOLS (+1.5, +2.5, -4.5)
    if any(t in texto_lower for t in ["ataque avassalador", "goleada", "placar elástico", "artilheiro"]):
        diagnostico["gols_over_2_5"]["possivel"] = True
        diagnostico["gols_over_2_5"]["motivo"] = "Termos indicam forte tendência a placar elástico e goleada."
    elif any(t in texto_lower for t in ["gols", "ofensiv", "marcou", "sofreu"]):
        diagnostico["gols_over_1_5"]["possivel"] = True
        diagnostico["gols_over_1_5"]["motivo"] = "Presença de movimentação ofensiva padrão ou histórico de gols citado."
        
    if any(t in texto_lower for t in ["defesa sólida", "retranca", "jogo fechado", "poucos gols", "foco defensivo", "amarrado", "empate"]):
        diagnostico["gols_under_4_5"]["possivel"] = True
        diagnostico["gols_under_4_5"]["motivo"] = "Jogo com tendência truncada ou focado em defesas. Margem segura para Under 4.5."
    else:
        diagnostico["gols_under_4_5"]["possivel"] = True
        diagnostico["gols_under_4_5"]["motivo"] = "Linha de segurança padrão aplicável para o cenário do confronto."

    # 4. MERCADO: BTTS (Ambos Marcam)
    if any(t in texto_lower for t in ["ambas marcam", "vulnerabilidade defensiva", "ambos os lados", "lá e cá", "troca de golpes", "vazada", "marcaram"]):
        diagnostico["btts"]["possivel"] = True
        diagnostico["btts"]["motivo"] = "Identificada troca de golpes ou fragilidades defensivas de ambos os lados."

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
            
    if diagnostico["chutes_no_gol_jogador"]["possivel"]:
        diagnostico["chutes_no_gol_jogador"]["motivo"] = "Presença de finalizadores de elite citados nominalmente ou em atividade no texto."

    # 6. MERCADO: QUANTIDADE DE CARTÕES
    if any(t in texto_lower for t in ["cartão", "cartões", "árbitro", "juiz", "faltoso", "clima tenso", "rivalidade", "truncado", "jogo duro", "disciplinar"]):
        diagnostico["quantidade_cartoes"]["possivel"] = True
        diagnostico["quantidade_cartoes"]["motivo"] = "Texto cita arbitragem rígida ou expectativa de jogo faltoso/nervoso."

    return diagnostico

def main():
    print("\n🤖 [INICIANDO SCRAPER DE SUMÁRIOS DA COPA - FILTRO POR DATA DO MAIN]")
    driver = configurar_driver()
    wait = WebDriverWait(driver, 5) # Espera curta e rápida de 5s
    
    hoje_ref = datetime.now()
    amanha_no_site = (hoje_ref + timedelta(days=1)).strftime("%d.%m.")
    
    url_calendario = "https://www.flashscore.com.br/futebol/mundo/campeonato-do-mundo/calendario/"
    
    try:
        print(f"🌍 Acessando o calendário de jogos da Copa: {url_calendario}")
        driver.get(url_calendario)
        time.sleep(5)
        
        elementos = driver.find_elements(By.CSS_SELECTOR, ".event__match")
        print(f"📦 Encontrados {len(elementos)} blocos de eventos totais no painel.")
        
        jogos_filtrados = []
        
        for el in elementos:
            try:
                # LÓGICA DE FILTRO EXTRAÍDA DO SEU MAIN.PY
                try:
                    tempo_el = el.find_element(By.CSS_SELECTOR, ".event__time")
                    tempo_raw = tempo_el.text.strip()
                except Exception:
                    continue

                if any(termo in tempo_raw for termo in ["Pên.", "Prorr.", "Enc.", "Intervalo", "Adiado"]):
                    continue

                partes_tempo = tempo_raw.split()
                if not partes_tempo:
                    continue
                    
                horario_str = partes_tempo[-1]
                if ":" not in horario_str:
                    continue

                h_obj = datetime.strptime(horario_str, "%H:%M")
                
                aceitar = False
                if amanha_no_site in tempo_raw:
                    if h_obj.hour <= 3: 
                        aceitar = True
                elif "." not in tempo_raw:
                    if (h_obj - timedelta(hours=3)).hour >= 7: 
                        aceitar = True

                if aceitar:
                    times = el.find_elements(By.CSS_SELECTOR, "span[class*='wcl-name'], .event__participant")
                    t1 = times[0].text.strip() if len(times) >= 1 else "Time Casa"
                    t2 = times[1].text.strip() if len(times) >= 2 else "Time Fora"
                    
                    id_jogo = el.get_attribute('id').split('_')[-1]
                    url_jogo = f"https://www.flashscore.com.br/jogo/{id_jogo}/"
                    
                    if url_jogo not in [j["url"] for j in jogos_filtrados]:
                        jogos_filtrados.append({
                            "id": id_jogo,
                            "casa": t1,
                            "fora": t2,
                            "url": url_jogo
                        })
            except Exception:
                continue
                
        print(f"🔥 Filtro de data aplicado! {len(jogos_filtrados)} jogos correspondem à janela operacional.\n")
        
        for jogo in jogos_filtrados:
            print("=" * 70)
            print(f"🏟️ ANALISANDO: {jogo['casa']} x {jogo['fora']}")
            print(f"🔗 URL: {jogo['url']}")
            print("-" * 70)
            
            try:
                driver.get(jogo['url'])
                
                elemento_texto = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, "[data-testid='fp-newsArticle-body'], .fp-body_9caht, .section--preview"
                )))
                
                try:
                    btn_mais = driver.find_element(By.CSS_SELECTOR, ".wclButtonLink--preview, [class*='previewShowMore']")
                    driver.execute_script("arguments[0].click();", btn_mais)
                    time.sleep(0.5)
                except:
                    pass 
                
                texto_sumario = driver.execute_script("return arguments[0].textContent;", elemento_texto).strip()
                print(f"📖 TEXTO EXTRAÍDO:\n\"{texto_sumario[:180]}... [Conteúdo Completo Lido]\"\n")
                
                analise = interpretar_texto(texto_sumario)
                
                print("📊 DIAGNÓSTICO DE MERCADOS MAPEADOS:")
                for mercado, dados in analise.items():
                    if dados["possivel"]:
                        print(f"  ✅ [{mercado.upper()}] - Ativado!")
                        if dados["motivo"]:
                            print(f"     ↳ Razão: {dados['motivo']}")
                        if "jogadores" in dados and dados["jogadores"]:
                            print(f"     ↳ Atletas Citados: {', '.join(dados['jogadores'])}")
                    else:
                        print(f"  ❌ [{mercado.upper()}] - Ignorado.")
                        
            except Exception:
                print(f"❌ Sumário indisponível para este jogo no momento.")
                
            print("=" * 70 + "\n")
            
    except Exception as e:
        print(f"🚨 Erro crítico na execução geral do Scraper: {e}")
    finally:
        driver.quit()
        print("🤖 [PROCESSO CONCLUÍDO]")

if __name__ == "__main__":
    main()
    
