"""
REGRAS DE GOLS - VERSÃO ENXUTA E RESTRITA
- Over: Mínimo 4/5 (>= 80%), apenas o maior (2.5 -> 1.5 -> 0.5)
- Under: Mínimo 4/5 (>= 80%), apenas o menor (-3.5 -> -4.5 -> -5.5)
- Regra de Ouro: Ou Over, ou Under (nunca ambos)
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    if c < 2 or f < 2:
        return 0

    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    elif c >= 3 and f >= 3:
        return 60
    else:
        return 40


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    c_15 = int(s.get("casa_15", 0) or 0)
    f_15 = int(s.get("fora_15", 0) or 0)
    
    if c_15 < 2 or f_15 < 2:
        return []

    # 1. Leitura de porcentagens de todos os mercados solicitados (mínimo 4/5 = 80%)
    pct_05 = calcular_porcentagem_gols(s.get("casa_05", 0), s.get("fora_05", 0))
    pct_15 = calcular_porcentagem_gols(c_15, f_15)
    pct_25 = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))
    
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m55 = calcular_porcentagem_gols(s.get("casa_55_under", 0), s.get("fora_55_under", 0))

    # Captura dos resultados do último jogo
    res_t1 = str(s.get("t1_resultado_1", "")).upper()
    res_t2 = str(s.get("t2_resultado_1", "")).upper()

    condicao_over_momento = (res_t1 == "V" and res_t2 == "D") or (res_t1 == "D" and res_t2 == "V")
    condicao_under_momento = (
        (res_t1 == "V" and res_t2 == "V") or 
        (res_t1 == "V" and res_t2 == "E") or 
        (res_t1 == "E" and res_t2 == "V") or 
        (res_t1 == "E" and res_t2 == "E")
    )

    m_pos = s.get("mandante_posicao")
    v_pos = s.get("visitante_posicao")

    overs_aprovados = []
    unders_aprovados = []

    tem_disparidade = False
    tem_proximidade = False

    if m_pos is not None and v_pos is not None:
        diferenca = abs(m_pos - v_pos)
        if diferenca >= 8:  
            tem_disparidade = True
        elif diferenca <= 3: 
            tem_proximidade = True

    # ==========================================================
    # AVALIAÇÃO DE OVERS (Mínimo 4/5 = 80%)
    # ==========================================================
    if condicao_over_momento:
        if m_pos is None or v_pos is None:
            if pct_25 >= 80:  
                overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})
            if pct_15 >= 80:
                overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
            if pct_05 >= 80:  
                overs_aprovados.append({"mercado": f"+0.5 Gols ({pct_05}%)", "tipo": "GOLS_05"})
        else:
            if pct_25 >= 80 and tem_disparidade:
                overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})
            if pct_15 >= 80 and (tem_disparidade or m_pos < 10 or not tem_proximidade):
                overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
            if pct_05 >= 80:
                overs_aprovados.append({"mercado": f"+0.5 Gols ({pct_05}%)", "tipo": "GOLS_05"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (Mínimo 4/5 = 80%)
    # ==========================================================
    if condicao_under_momento:
        if pct_m35 >= 80:
            unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
        if pct_m45 >= 80:
            unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})
        if pct_m55 >= 80:
            unders_aprovados.append({"mercado": f"-5.5 Gols ({pct_m55}%)", "tipo": "GOLS_M55"})

    # ==========================================================
    # APLICAÇÃO DAS REGRAS DE SELEÇÃO ÚNICA E PRIORIDADE
    # ==========================================================
    
    # 1. Se achou Over, pega apenas O MAIOR (o primeiro da lista, pois ordenamos de 2.5 para 0.5)
    if overs_aprovados:
        return [overs_aprovados[0]]
    
    # 2. Se não tem over mas tem under, pega apenas O MENOR (o primeiro da lista, ordenado de -3.5 para -5.5)
    elif unders_aprovados:
        return [unders_aprovados[0]]
    
    return []
