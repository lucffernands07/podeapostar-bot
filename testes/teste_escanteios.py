#testes/teste_escanteios.py

import re

# 🟢 LISTA BRANCA: Ligas qualificadas para análise de estatísticas de equipe
LIGAS_ELITE_ESCANT_EIOS = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def analisar_dados_escanteios(cantos_mandante_h2h, cantos_visitante_h2h, nome_liga="", quantidade_jogos=3):
    """
    Processa os históricos de escanteios totais (soma de casa+fora) coletados na nova raspagem.
    Calcula as médias reais dos jogos anteriores de cada equipe e define a linha ideal.
    """
    # 🚀 TRAVA DE LIGA ELITE
    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_ESCANT_EIOS:
        liga_print = nome_liga_limpo if nome_liga_limpo else "NOME_DA_LIGA_VAZIO"
        print(f"⏩ [TRAVA] Pulando análise de escanteios para a liga '{liga_print}' (Não é considerada liga Elite).")
        return {"aprovado": False}

    # Garante que possuímos a amostragem completa de jogos passados exigida
    if len(cantos_mandante_h2h) < quantidade_jogos or len(cantos_visitante_h2h) < quantidade_jogos:
        print(f"⏩ [HISTÓRICO INCOMPLETO] Dados de escanteios insuficientes para o confronto.")
        return {"aprovado": False}

    # Como cada item já representa o total de cantos daquela partida do h2h:
    jogos_mandante_total = cantos_mandante_h2h[:quantidade_jogos]
    jogos_visitante_total = cantos_visitante_h2h[:quantidade_jogos]

    # --- CÁLCULO DAS MÉDIAS REAIS ---
    # Soma de todos os cantos vistos nos 6 jogos somados (3 do mandante + 3 do visitante) dividido por 6
    total_cantos_acumulados = sum(jogos_mandante_total) + sum(jogos_visitante_total)
    media_geral_confronto = total_cantos_acumulados / (quantidade_jogos * 2)

    # Média isolada de cada histórico para o log de auditoria
    media_historico_mandante = sum(jogos_mandante_total) / quantidade_jogos
    media_historico_visitante = sum(jogos_visitante_total) / quantidade_jogos

    # 📊 DEFINIÇÃO DA LINHA BASE FLUTUANTE
    if media_geral_confronto >= 10.5:
        linha_base = 9.5
        sinal = "+"
    elif media_geral_confronto >= 9.0:
        linha_base = 8.5
        sinal = "+"
    elif media_geral_confronto >= 7.5:
        linha_base = 7.5
        sinal = "+"
    else:
        # Jogos com tendência severa de under cantos
        linha_base = 10.5
        sinal = "-"

    # 🟢 APLICAÇÃO DA REGRA DE MARGEM DE SEGURANÇA
    if sinal == "-":
        linha_final = linha_base  
        texto_mercado = f"Escanteios: Menos de {linha_final}"
    else:
        linha_final = linha_base  
        texto_mercado = f"Escanteios: Mais de {linha_final}"

    # Log detalhado para auditoria visual no terminal
    log_detalhado = (
        f"  🏟️ {nome_liga_limpo}\n"
        f"  ➔ Média nos jogos do Mandante: {media_historico_mandante:.2f} cantos {jogos_mandante_total}\n"
        f"  ➔ Média nos jogos do Visitante: {media_historico_visitante:.2f} cantos {jogos_visitante_total}\n"
        f"  ➔ Média Geral Combinada: {media_geral_confronto:.2f}\n"
    )

    return {
        "aprovado": True,
        "total_mandante": sum(jogos_mandante_total),
        "total_visitante": sum(jogos_visitante_total),
        "total_confronto": total_cantos_acumulados,
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_cantos": log_detalhado
    }
    
