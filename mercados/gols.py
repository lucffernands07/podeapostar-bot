"""
REGRAS DE GOLS - ATUALIZADO COM AS NOVAS REGRAS DE FREQUÊNCIA E PRIORIDADE
- Prioridade: +2.5 -> +1.5 -> -4.5 -> -3.5 -> +0.5
"""

def contar_jogos_com_gols(lista_gols, condicao, valor_alvo):
    """
    Função auxiliar para contar em quantos jogos da lista a condição foi atingida.
    Ex: condicao '>=' e valor_alvo '2'.
    """
    if not isinstance(lista_gols, list) or not lista_gols:
        return 0
    
    count = 0
    for g in lista_gols:
        try:
            val = int(g)
            if condicao == ">=" and val >= valor_alvo:
                count += 1
            elif condicao == "<=" and val <= valor_alvo:
                count += 1
        except:
            continue
    return count


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # Extração das listas de gols dos últimos jogos (mandante em casa e visitante fora)
    # Supondo que o dicionário traga listas ou os valores isolados _1, _2, _3, _4, _5
    # Vamos montar as listas a partir das chaves individuais para garantir compatibilidade:
    try:
        gols_mandante = [
            int(s.get("t1_gols_favor_1", 0) or 0),
            int(s.get("t1_gols_favor_2", 0) or 0),
            int(s.get("t1_gols_favor_3", 0) or 0),
            int(s.get("t1_gols_favor_4", 0) or 0),
            int(s.get("t1_gols_favor_5", 0) or 0)
        ]
    except:
        gols_mandante = []

    try:
        gols_visitante = [
            int(s.get("t2_gols_favor_1", 0) or 0),
            int(s.get("t2_gols_favor_2", 0) or 0),
            int(s.get("t2_gols_favor_3", 0) or 0),
            int(s.get("t2_gols_favor_4", 0) or 0),
            int(s.get("t2_gols_favor_5", 0) or 0)
        ]
    except:
        gols_visitante = []

    if not gols_mandante or not gols_visitante:
        return []

    # ==========================================================
    # AVALIAÇÃO DAS CONDIÇÕES DA SUA NOVA REGRA (Mínimo 4/5 jogos)
    # ==========================================================

    # +0.5: casa >= 1 gols em >= 4/5 OU fora >= 2 gols em >= 4/5
    m_mais_05 = contar_jogos_com_gols(gols_mandante, ">=", 1) >= 4
    v_mais_05 = contar_jogos_com_gols(gols_visitante, ">=", 2) >= 4
    valida_05 = m_mais_05 or v_mais_05

    # +1.5: casa >= 2 gols em >= 4/5 OU fora >= 3 gols em >= 4/5
    m_mais_15 = contar_jogos_com_gols(gols_mandante, ">=", 2) >= 4
    v_mais_15 = contar_jogos_com_gols(gols_visitante, ">=", 3) >= 4
    valida_15 = m_mais_15 or v_mais_15

    # +2.5: casa >= 3 gols em >= 4/5 OU fora >= 4 gols em >= 4/5
    m_mais_25 = contar_jogos_com_gols(gols_mandante, ">=", 3) >= 4
    v_mais_25 = contar_jogos_com_gols(gols_visitante, ">=", 4) >= 4
    valida_25 = m_mais_25 or v_mais_25

    # -3.5: casa <= 2 gols em >= 4/5 E fora <= 1 gol em >= 4/5
    m_menos_35 = contar_jogos_com_gols(gols_mandante, "<=", 2) >= 4
    v_menos_35 = contar_jogos_com_gols(gols_visitante, "<=", 1) >= 4
    valida_m35 = m_menos_35 and v_menos_35

    # -4.5: casa <= 2 gols em >= 4/5 E fora <= 2 gols em >= 4/5
    m_menos_45 = contar_jogos_com_gols(gols_mandante, "<=", 2) >= 4
    v_menos_45 = contar_jogos_com_gols(gols_visitante, "<=", 2) >= 4
    valida_m45 = m_menos_45 and v_menos_45

    # ==========================================================
    # ORDEM DE PRIORIDADE ESTABELECIDA (Retorna APENAS 1)
    # Prioridade: +2.5 -> +1.5 -> -4.5 -> -3.5 -> +0.5
    # ==========================================================

    if valida_25:
        return [{"mercado": "+2.5 Gols", "tipo": "GOLS_25"}]
    
    if valida_15:
        return [{"mercado": "+1.5 Gols", "tipo": "GOLS_15"}]
    
    if valida_m45:
        return [{"mercado": "-4.5 Gols", "tipo": "GOLS_M45"}]
    
    if valida_m35:
        return [{"mercado": "-3.5 Gols", "tipo": "GOLS_M35"}]
    
    if valida_05:
        return [{"mercado": "+0.5 Gols", "tipo": "GOLS_05"}]

    return []
    
