import re
from . import jogadores  

def analisar_dados_cartoes(cartoes_mandante_h2h, cartoes_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"
    
    permite_coletivos = jogadores.validar_liga_para_jogadores(nome_liga_limpo)
    if not permite_coletivos:
        print(f"      ⏩ [OTIMIZAÇÃO CARTÕES] Pulando média de cartões para {nome_liga_limpo} (Não é liga Elite).")
        return {"aprovado": False}

    lista_mandante = cartoes_mandante_h2h if isinstance(cartoes_mandante_h2h, list) else []
    lista_visitante = cartoes_visitante_h2h if isinstance(cartoes_visitante_h2h, list) else []

    if len(lista_mandante) < quantidade_jogos or len(lista_visitante) < quantidade_jogos:
        print(f"⏩ [HISTÓRICO INCOMPLETO] Dados de cartões insuficientes para o confronto.")
        return {"aprovado": False}

    try:
        raw_mandante = [int(str(x).strip()) for x in lista_mandante[:quantidade_jogos]]
        raw_visitante = [int(str(x).strip()) for x in lista_visitante[:quantidade_jogos]]
    except Exception as e_conv:
        print(f"⚠️ [ERRO CONVERSÃO] Erro ao converter dados de cartões para números: {e_conv}")
        return {"aprovado": False}

    if dados_incompletos:
        print(f"⏩ [DESCARTADO CARTÕES] Flag de dados incompletos ativada para {nome_liga_limpo}.")
        return {"aprovado": False}

    # 🟢 NOVO FILTRO CRUZADO: Descarta a partida APENAS se AMBOS forem 0 no mesmo jogo.
    # Caso contrário, o time que registrou cartões entra normalmente no cálculo.
    jogos_mandante = []
    jogos_visitante = []

    for m_val, v_val in zip(raw_mandante, raw_visitante):
        if m_val == 0 and v_val == 0:
            continue # Descarta apenas se ambos zeraram na mesma partida
        jogos_mandante.append(m_val)
        jogos_visitante.append(v_val)

    # Valida se após o filtro cruzado ainda sobrou a quantidade mínima exigida de jogos
    if len(jogos_mandante) < quantidade_jogos or len(jogos_visitante) < quantidade_jogos:
        print(f"⏩ [HISTÓRICO INCOMPLETO] Jogos insuficientes após o filtro de zeros em cartões.")
        return {"aprovado": False}

    # Avaliação isolada por time para permitir o filtro separado
    aprovado_mandante = False
    aprovado_visitante = False

    # 1. Mandante
    if not any(m == 0 for m in jogos_mandante):
        media_mandante = sum(jogos_mandante) / quantidade_jogos
        if media_mandante >= 0.5: # Critério individual ajustável
            aprovado_mandante = True

    # 2. Visitante
    if not any(v == 0 for v in jogos_visitante):
        media_visitante = sum(jogos_visitante) / quantidade_jogos
        if media_visitante >= 0.5: # Critério individual ajustável
            aprovado_visitante = True

    if not aprovado_mandante and not aprovado_visitante:
        return {"aprovado": False}

    total_mandante = sum(jogos_mandante)
    total_visitante = sum(jogos_visitante)
    media_geral_confronto = (total_mandante + total_visitante) / quantidade_jogos

    if media_geral_confronto < 1.0:
        print(f"⏩ [REJEITADO] Média de cartões muito baixa ({media_geral_confronto:.2f}). Confronto descartado.")
        return {"aprovado": False}

    texto_mercado = f"Média Cartões: {media_geral_confronto:.1f}"

    return {
        "aprovado": True,
        "tipo": "CARTOES_GERAL", 
        "tipo_mandante": "CARTOES_MANDANTE",
        "tipo_visitante": "CARTOES_VISITANTE",
        "aprovado_mandante": aprovado_mandante,
        "aprovado_visitante": aprovado_visitante,
        "total_mandante": total_mandante,
        "total_visitante": total_visitante,
        "total_confronto": total_mandante + total_visitante, 
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_jogadores": "" 
    }
    
