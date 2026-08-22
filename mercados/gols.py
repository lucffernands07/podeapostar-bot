"""
REGRAS DE GOLS - SUPERSCORE (BASEADO NAS MÉDIAS DA ABA ESTATÍSTICAS)
"""

def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # Captura as médias de gols do mandante e visitante vindas do Superscore
    mg_mandante = float(s.get("media_gols_mandante", 0.0) or 0.0)
    mg_visitante = float(s.get("media_gols_visitante", 0.0) or 0.0)

    overs_aprovados = []
    unders_aprovados = []

    # ==========================================================
    # 🟢 REGRAS DE OVERS (+1.5 Gols)
    # ==========================================================
    # Ordem decrescente de porcentagem (95% -> 85% -> 75%)
    if (1.8 <= mg_mandante <= 1.9) and (1.8 <= mg_visitante <= 1.9):
        overs_aprovados.append({"mercado": "+1.5 Gols (95%)", "tipo": "GOLS_15"})
    elif (1.4 <= mg_mandante <= 1.7) and (1.4 <= mg_visitante <= 1.7):
        overs_aprovados.append({"mercado": "+1.5 Gols (85%)", "tipo": "GOLS_15"})
    elif (1.0 <= mg_mandante <= 1.3) and (1.0 <= mg_visitante <= 1.3):
        overs_aprovados.append({"mercado": "+1.5 Gols (75%)", "tipo": "GOLS_15"})


    # ==========================================================
    # 🟢 REGRAS DE OVERS (+2.5 Gols)
    # Um dos times tem média >= 2.0 e o outro entra na faixa secundária
    # ==========================================================
    tem_time_alto = (mg_mandante >= 2.0) or (mg_visitante >= 2.0)
    
    if tem_time_alto:
        # Pega a média do "outro" time (o que não é o >= 2.0, ou qualquer um se ambos forem >= 2.0)
        outro_time = mg_visitante if mg_mandante >= 2.0 else mg_mandante
        
        if 1.8 <= outro_time <= 1.9:
            overs_aprovados.append({"mercado": "+2.5 Gols (95%)", "tipo": "GOLS_25"})
        elif 1.4 <= outro_time <= 1.7:
            overs_aprovados.append({"mercado": "+2.5 Gols (85%)", "tipo": "GOLS_25"})
        elif 1.0 <= outro_time <= 1.3:
            overs_aprovados.append({"mercado": "+2.5 Gols (75%)", "tipo": "GOLS_25"})


    # ==========================================================
    # 🔴 REGRAS DE UNDERS (-4.5 Gols)
    # Um time fixo em 1.0 e o outro variando
    # ==========================================================
    # Usamos uma margem de tolerância pequena (ex: 0.95 a 1.05) para garantir a leitura exata do float
    eh_um_ponto_zero_1 = (0.95 <= mg_mandante <= 1.05)
    eh_um_ponto_zero_2 = (0.95 <= mg_visitante <= 1.05)
    
    if eh_um_ponto_zero_1 or eh_um_ponto_zero_2:
        outro_under_45 = mg_visitante if eh_um_ponto_zero_1 else mg_mandante
        
        if outro_under_45 <= 0.5:
            unders_aprovados.append({"mercado": "-4.5 Gols (95%)", "tipo": "GOLS_M45"})
        elif outro_under_45 <= 1.0:
            unders_aprovados.append({"mercado": "-4.5 Gols (85%)", "tipo": "GOLS_M45"})
        elif outro_under_45 >= 1.5:
            unders_aprovados.append({"mercado": "-4.5 Gols (75%)", "tipo": "GOLS_M45"})


    # ==========================================================
    # 🔴 REGRAS DE UNDERS (-3.5 Gols)
    # Um time < 1.0 e o outro <= limite
    # ==========================================================
    tem_baixo = (mg_mandante < 1.0) or (mg_visitante < 1.0)
    
    if tem_baixo:
        outro_under_35 = mg_visitante if mg_mandante < 1.0 else mg_mandante
        
        if outro_under_35 <= 1.0:
            unders_aprovados.append({"mercado": "-3.5 Gols (95%)", "tipo": "GOLS_M35"})
        elif outro_under_35 <= 1.5:
            unders_aprovados.append({"mercado": "-3.5 Gols (85%)", "tipo": "GOLS_M35"})
        elif outro_under_35 <= 2.0:
            unders_aprovados.append({"mercado": "-3.5 Gols (75%)", "tipo": "GOLS_M35"})


    # ==========================================================
    # RETORNO SEGURO 
    # ==========================================================
    if overs_aprovados:
        return overs_aprovados
    elif unders_aprovados:
        return unders_aprovados
    
    return []
