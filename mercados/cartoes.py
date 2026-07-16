import re

def analisar_dados_cartoes(cartoes_mandante_h2h, cartoes_visitante_h2h, nome_liga="", quantidade_jogos=3):
    """
    Processa os históricos coletivos de cartões amarelos obtidos no H2H.
    Calcula a média geral somando os cartões de ambos os times nos últimos jogos.
    """
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"
    
    # 🚫 TRAVA DE LIGA ELITE REMOVIDA DAQUI PARA DEIXAR RASPAGEM LIVRE

    # Garante que os parâmetros sejam listas válidas e não nulas
    lista_mandante = cartoes_mandante_h2h if isinstance(cartoes_mandante_h2h, list) else []
    lista_visitante = cartoes_visitante_h2h if isinstance(cartoes_visitante_h2h, list) else []

    # Se ambas as listas vierem completamente vazias da raspagem, já reprova de cara
    if not lista_mandante and not lista_visitante:
        print(f"⏩ [REJEITADO] Sem dados de cartões disponíveis para o confronto.")
        return {"aprovado": False}

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

    # 🛑 REGRA DE SEGURANÇA: Descarta se a média combinada de cartões for menor que 1.0
    # Evita dados zerados (0.0) ou insuficientes na geração do bilhete
    if media_geral_confronto < 1.0:
        print(f"⏩ [REJEITADO] Média de cartões muito baixa ({media_geral_confronto:.2f}). Confronto descartado.")
        return {"aprovado": False}

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
    
