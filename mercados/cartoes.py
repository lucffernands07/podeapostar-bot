import re
from . import jogadores  # Importa o módulo onde fica a trava de validação de liga elite

def analisar_dados_cartoes(cartoes_mandante_h2h, cartoes_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    """
    Processa os históricos coletivos de cartões amarelos obtidos no H2H.
    Calcula a média geral somando os cartões de ambos os times nos últimos jogos se for liga elite.
    """
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"
    
    # 🟢 TRAVA DE SEGURANÇA: Validação da Liga Elite antes de processar
    permite_coletivos = jogadores.validar_liga_para_jogadores(nome_liga_limpo)
    if not permite_coletivos:
        print(f"      ⏩ [OTIMIZAÇÃO CARTÕES] Pulando média de cartões para {nome_liga_limpo} (Não é liga Elite).")
        return {"aprovado": False}

    # Garante que os parâmetros sejam listas válidas e não nulas
    lista_mandante = cartoes_mandante_h2h if isinstance(cartoes_mandante_h2h, list) else []
    lista_visitante = cartoes_visitante_h2h if isinstance(cartoes_visitante_h2h, list) else []

    # Se ambas as listas vierem incompletas em número de jogos
    if len(lista_mandante) < quantidade_jogos or len(lista_visitante) < quantidade_jogos:
        print(f"⏩ [HISTÓRICO INCOMPLETO] Dados de cartões insuficientes para o confronto.")
        return {"aprovado": False}

    # 🚨 BLINDAGEM: Converte todos os valores extraídos para INT limpando possíveis espaços ou strings
    try:
        jogos_mandante = [int(str(x).strip()) for x in lista_mandante[:quantidade_jogos]]
        jogos_visitante = [int(str(x).strip()) for x in lista_visitante[:quantidade_jogos]]
    except Exception as e_conv:
        print(f"⚠️ [ERRO CONVERSÃO] Erro ao converter dados de cartões para números: {e_conv}")
        return {"aprovado": False}

    # 🛑 🚨 TRAVA DE DADOS ZERADOS/INCOMPLETOS:
    # 1. Checa a flag do scraper
    if dados_incompletos:
        print(f"⏩ [DESCARTADO CARTÕES] Flag de dados incompletos ativada para {nome_liga_limpo}.")
        return {"aprovado": False}

    # 2. Checa se o TOTAL COMBINADO da partida deu 0 (0 + 0 = 0 cartões na partida)
    for m, v in zip(jogos_mandante, jogos_visitante):
        if (m + v) == 0:
            print(f"⏩ [DESCARTADO CARTÕES] Partida com total de cartões zerado ({m} + {v} = 0) para {nome_liga_limpo}.")
            return {"aprovado": False}

    # Soma todos os cartões amarelos do período de cada equipe
    total_mandante = sum(jogos_mandante)
    total_visitante = sum(jogos_visitante)

    # Calcula as médias por partida de cada equipe
    media_mandante = total_mandante / quantidade_jogos
    media_visitante = total_visitante / quantidade_jogos
    
    # Média combinada do confronto
    media_geral_confronto = media_mandante + media_visitante

    # 🛑 REGRA DE SEGURANÇA: Descarta se a média combinada de cartões for menor que 1.0
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
    
