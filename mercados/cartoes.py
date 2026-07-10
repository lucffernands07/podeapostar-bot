import re

# 🟢 LISTA BRANCA: Apenas ligas de elite que comprovadamente abrem mercados de cartões na Betano
LIGAS_ELITE_CARTOES = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Europa - Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def analisar_dados_cartoes(cartoes_mandante_h2h, cartoes_visitante_h2h, nome_liga="", quantidade_jogos=3):
    """
    Processa os históricos coletivos de cartões amarelos obtidos no H2H.
    Calcula a média geral somando os cartões de ambos os times nos últimos jogos.
    """
    # 🚀 TRAVA DE LIGA ELITE
    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_CARTOES:
        liga_print = nome_liga_limpo if nome_liga_limpo else "NOME_DA_LIGA_VAZIO"
        print(f"⏩ [TRAVA] Pulando análise de cartões para a liga '{liga_print}' (Não é considerada liga Elite ou string inválida).")
        return {}

    # Garante que os parâmetros sejam listas válidas e não nulas
    lista_mandante = cartoes_mandante_h2h if isinstance(cartoes_mandante_h2h, list) else []
    lista_visitante = cartoes_visitante_h2h if isinstance(cartoes_visitante_h2h, list) else []

    # Recorta ou garante o tamanho exato de jogos coletados para a média (padrão: últimos 3 jogos)
    jogos_mandante = lista_mandante[:quantidade_jogos]
    jogos_visitante = lista_visitante[:quantidade_jogos]

    # Soma todos os cartões amarelos do período de cada equipe
    total_mandante = sum(jogos_mandante)
    total_visitante = sum(jogos_visitante)

    # Calcula as médias por partida de cada equipe
    media_mandante = total_mandante / len(jogos_mandante) if len(jogos_mandante) > 0 else 0
    media_visitante = total_visitante / len(jogos_visitante) if len(jogos_visitante) > 0 else 0
    
    # Média combinada do confronto
    media_geral_confronto = media_mandante + media_visitante

    # Formatação limpa para o listão
    texto_mercado = f"Média Cartões: {media_geral_confronto:.1f}"

    return {
        "aprovado": True,
        "total_mandante": total_mandante,
        "total_visitante": total_visitante,
        "total_confronto": total_mandante + total_visitante, 
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_jogadores": "" # Removido para manter enxuto
    }
    
