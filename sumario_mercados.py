import re
import time
import os
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
    print("\n🤖 [INICIANDO SCRAPER DE SUMÁRIOS]")
    driver = configurar_driver()
    wait = WebDriverWait(driver, 12)
    
    # Lista de URLs que você deseja analisar diretamente
    # Você pode colocar múltiplas URLs aqui dentro se quiser analisar vários jogos em lote
    urls_para_analisar = [
        "https://www.flashscore.com.br/jogo/futebol/argentina-f9OppQjp/austria-naHiWdnt/"
    ]
    
    for url in urls_para_analisar:
        print("=" * 70)
        print(f"🔗 ACESSANDO URL: {url}")
        print("-" * 70)
        
        try:
            driver.get(url)
            
            # 1. Localiza o contêiner do artigo com base na estrutura real do HTML enviado
            elemento_texto = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "[data-testid='fp-newsArticle-body'], .fp-body_9caht, .section--preview"
            )))
            
            # 2. Tenta expandir clicando no botão "Mostrar pré-jogo detalhado" (classe exata do HTML: .wclButtonLink--preview)
            try:
                btn_mais = driver.find_element(By.CSS_SELECTOR, ".wclButtonLink--preview, [class*='previewShowMore']")
                driver.execute_script("arguments[0].click();", btn_mais)
                time.sleep(0.5)
            except:
                pass # Se já estiver expandido ou não tiver o botão, segue a vida
            
            # 3. Extrai o conteúdo em texto puro limpo
            texto_sumario = driver.execute_script("return arguments[0].textContent;", elemento_texto).strip()
            
            print(f"📖 TEXTO EXTRAÍDO COM SUCESSO:\n\"{texto_sumario}\"\n")
            
            # 4. Processa no motor de palavras-chave
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
                    
        except Exception as e:
            print(f"🚨 Erro ao raspar esta partida: {e}")
            
        print("=" * 70 + "\n")
        
    driver.quit()
    print("🤖 [PROCESSO CONCLUÍDO]")

if __name__ == "__main__":
    main()
        
