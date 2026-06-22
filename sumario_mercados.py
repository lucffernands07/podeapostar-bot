import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_e_interpretar_sumario(driver, url_jogo):
    """
    Acessa a aba principal do jogo, extrai o texto descritivo do Sumário
    e faz a varredura por Inteligência de Texto para mapear os mercados possíveis.
    """
    # Abre o jogo em uma nova aba para não perder a navegação principal
    driver.execute_script(f"window.open('{url_jogo}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    texto_sumario = ""
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Seletores mapeados para capturar a Pré-visualização/Descrição do Flashscore
        elemento_texto = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, ".previewShowMore, [class*='previewDescription'], [class*='previewText']"
        )))
        
        # Força o clique no "Mostrar pré-jogo detalhado" se ele existir para pegar o texto completo
        try:
            btn_mais = driver.find_element(By.CSS_SELECTOR, ".previewShowMore__button, [class*='showMore']")
            driver.execute_script("arguments[0].click();", btn_mais)
            time.sleep(0.5)
        except:
            pass # Se não houver botão de expandir, lê o texto que já está visível
            
        texto_sumario = driver.execute_script("return arguments[0].textContent;", elemento_texto).strip()
        
    except Exception as e:
        print(f"⚠️ Não foi possível ler o texto descritivo do sumário: {e}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return {}

    # Fecha a aba do jogo e volta para a principal
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    # --- 🤖 MOTOR DE INTERPRETAÇÃO TEXTUAL DE MERCADOS ---
    texto_lower = texto_sumario.lower()
    
    # Estrutura base de retorno para o robô principal decidir quais mercados processar
    diagnostico = {
        "texto_bruto": texto_sumario,
        "vitoria": {"possivel": False, "motivo": "", "chave": "1X2"},
        "dupla_chance": {"possivel": False, "motivo": "", "chave": "CHANCE_DUPLA"},
        "quantidade_gols": {"possivel": False, "motivo": "", "chave": "GOLS"},
        "btts": {"possivel": False, "motivo": "", "chave": "BTTS"},
        "chutes_no_gol_jogador": {"possivel": False, "jogadores_citados": [], "chave": "CHUTES_ALVO"},
        "quantidade_cartoes": {"possivel": False, "motivo": "", "chave": "CARTOES"}
    }

    # 1. MERCADO: VITÓRIA
    if any(t in texto_lower for t in ["favorit", "franco favor", "dominar", "superioridade", "vencer confortavelmente"]):
        diagnostico["vitoria"]["possivel"] = True
        diagnostico["vitoria"]["motivo"] = "Texto indica favoritismo ou superioridade acentuada."

    # 2. MERCADO: DUPLA CHANCE
    if any(t in texto_lower for t in ["equilibrad", "confronto parelho", "tendência de empate", "equipes se equivalem", "jogo duro"]):
        diagnostico["dupla_chance"]["possivel"] = True
        diagnostico["dupla_chance"]["motivo"] = "Jogo muito parelho ou truncado, sugerindo proteção com Dupla Chance."
    elif diagnostico["vitoria"]["possivel"]:
        diagnostico["dupla_chance"]["possivel"] = True
        diagnostico["dupla_chance"]["motivo"] = "Favorito identificado; opção de Dupla Chance de segurança (1X ou X2)."

    # 3. MERCADO: QUANTIDADE DE GOLS (Over / Under)
    if any(t in texto_lower for t in ["ataque avassalador", "goleada", "gols", "ofensiv", "placar elástico", "artilheiro"]):
        diagnostico["quantidade_gols"]["possivel"] = True
        diagnostico["quantidade_gols"]["motivo"] = "Indicação de forte presença ofensiva (Tendência de Over)."
    elif any(t in texto_lower for t in ["defesa sólida", "retranca", "jogo fechado", "poucos gols", "foco defensivo", "amarrado"]):
        diagnostico["quantidade_gols"]["possivel"] = True
        diagnostico["quantidade_gols"]["motivo"] = "Análise aponta forte consistência defensiva ou jogo travado (Tendência de Under)."

    # 4. MERCADO: BTTS (Ambos Marcam)
    if any(t in texto_lower for t in ["ambas marcam", "vulnerabilidade defensiva", "ambos os lados", "lá e cá", "troca de golpes", "vazada"]):
        diagnostico["btts"]["possivel"] = True
        diagnostico["btts"]["motivo"] = "O analista citou fragilidades defensivas em ambos os lados ou estilo 'lá e cá'."

    # 5. MERCADO: CHUTES NO GOL DE JOGADOR
    # Lista de monitoramento para estrelas e termos de finalização
    estrelas_copa = ["messi", "ronaldo", "mbappé", "bellingham", "vinicius", "haaland", "kane", "griezmann", "lewandowski"]
    for estrela in estrelas_copa:
        if estrela in texto_lower:
            diagnostico["chutes_no_gol_jogador"]["possivel"] = True
            diagnostico["chutes_no_gol_jogador"]["jogadores_citados"].append(estrela.capitalize())
            
    if any(t in texto_lower for t in ["inspirado", "finalizador", "chuta muito", "chutes", "finalizações"]):
        diagnostico["chutes_no_gol_jogador"]["possivel"] = True
        if not diagnostico["chutes_no_gol_jogador"]["jogadores_citados"]:
            diagnostico["chutes_no_gol_jogador"]["jogadores_citados"].append("Destaque Ofensivo Citado")

    # 6. MERCADO: QUANTIDADE DE CARTÕES
    if any(t in texto_lower for t in ["cartão", "cartões", "árbitro", "juiz", "faltoso", "clima tenso", "rivalidade", "truncado", "jogo duro", "disciplinar"]):
        diagnostico["quantidade_cartoes"]["possivel"] = True
        diagnostico["quantidade_cartoes"]["motivo"] = "Mencionou arbitragem rigorosa ou expectativa de jogo tenso/faltoso."

    return diagnostico
