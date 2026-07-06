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
    Processa os históricos brutos de escanteios coletados na aba de estatísticas totais.
    Calcula as médias reais quando o mandante joga em casa e o visitante joga fora.
    Retorna o mercado dinâmico ideal de linhas de cantos.
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

    # Recorta cirurgicamente as últimas 3 partidas de cada um nas suas respectivas condições
    jogos_casa = cantos_mandante_h2h[:quantidade_jogos]
    jogos_fora = cantos_visitante_h2h[:quantidade_jogos]

    total_mandante = sum(jogos_casa)
    total_visitante = sum(jogos_fora)

    # --- CÁLCULO DAS MÉDIAS REAIS ---
    media_mandante = total_mandante / quantidade_jogos
    media_visitante = total_visitante / quantidade_jogos
    media_geral_confronto = media_mandante + media_visitante

    # 📊 DEFINIÇÃO DA LINHA BASE FLUTUANTE (VALOR NUMÉRICO COM SINAL COMERCIAL)
    # Ex: Se a somatória das médias for muito alta, buscamos o Over 8.5, se for padrão, Over 7.5
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

    # 🟢 APLICAÇÃO DA REGRA DE MARGEM DE SEGURANÇA (Ajustando 1.0 para linhas comerciais padrão)
    if sinal == "-":
        linha_final = linha_base  # Para Under, mantém a linha limite alta com margem
        texto_mercado = f"Escanteios: Menos de {linha_final}"
    else:
        linha_final = linha_base  # Para Over, define o gatilho de entrada seguro
        texto_mercado = f"Escanteios: Mais de {linha_final}"

    # Log detalhado para auditoria visual no terminal
    log_detalhado = (
        f"  🏟️ {nome_liga_limpo}\n"
        f"  ➔ Média Mandante (Casa): {media_mandante:.2f} cantos {jogos_casa}\n"
        f"  ➔ Média Visitante (Fora): {media_visitante:.2f} cantos {jogos_fora}\n"
        f"  ➔ Média Combinada: {media_geral_confronto:.2f}\n"
    )

    return {
        "aprovado": True,
        "total_mandante": total_mandante,
        "total_visitante": total_visitante,
        "total_confronto": total_mandante + total_visitante,
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_cantos": log_detalhado
    }
