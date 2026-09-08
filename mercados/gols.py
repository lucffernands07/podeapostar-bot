"""
REGRAS DE GOLS - ATUALIZADO COM NOVA ORDEM DE PRIORIDADE
- Sequência de Prioridade: +2.5 -> +1.5 -> -4.5 -> -3.5 -> +0.5
- Regra do 0x0: Se houve 0x0 recente, o mercado escolhido será sempre o -4.5 (se disponível).
- Over +0.5: Só entra se NÃO houver -3.5 e nem -4.5 aprovados.
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

    # 1. Leitura direta das porcentagens dos 5 jogos
    pct_05 = calcular_porcentagem_gols(s.get("casa_05", 0), s.get("fora_05", 0))
    pct_15 = calcular_porcentagem_gols(c_15, f_15)
    pct_25 = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))
    
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m55 = calcular_porcentagem_gols(s.get("casa_55_under", 0), s.get("fora_55_under", 0))

    # Checagem de 0x0 no último jogo (mandante em casa ou visitante fora)
    placar_casa_ult = str(s.get("t1_placar_1", "")).replace(" ", "")
    placar_fora_ult = str(s.get("t2_placar_1", "")).replace(" ", "")
    
    teve_zero_a_zero = ("0-0" in placar_casa_ult or "0x0" in placar_casa_ult or 
                        "0-0" in placar_fora_ult or "0x0" in placar_fora_ult)

    gols_c_ult = s.get("t1_gols_favor_1")
    gols_f_ult = s.get("t2_gols_favor_1")
    if (gols_c_ult == 0 and s.get("t1_gols_contra_1") == 0) or (gols_f_ult == 0 and s.get("t2_gols_contra_1") == 0):
        teve_zero_a_zero = True

    # ==========================================================
    # VALIDAÇÃO DOS MERCADOS INDIVIDUAIS
    # ==========================================================
    
    # +2.5 Gols (Regra de resultado mandante/visitante + estatística >= 80%)
    casa_25_qtd = int(s.get("casa_25", 0) or 0)
    fora_25_qtd = int(s.get("fora_25", 0) or 0)
    mandante_ok_25 = (casa_25_qtd >= 4) and (int(s.get("mandante_sem_derrota_casa", 0) or 0) >= 4)
    vis_vitorias = int(s.get("visitante_vitorias_fora", 0) or 0)
    vis_derrotas = int(s.get("visitante_derrotas_fora", 0) or 0)
    vis_empates = max(0, 5 - (vis_vitorias + vis_derrotas))
    visitante_ok_25 = (fora_25_qtd >= 4) and ((vis_derrotas + vis_empates) >= 4)
    
    valida_25 = (mandante_ok_25 and visitante_ok_25 and pct_25 >= 80)

    # +1.5 Gols (Estatística >= 80% + mandante fez >= 1 gol no último jogo em casa)
    mandante_fez_gol_ult = False
    try:
        if placar_casa_ult and "-" in placar_casa_ult:
            if int(placar_casa_ult.split("-")[0]) >= 1:
                mandante_fez_gol_ult = True
        elif gols_c_ult is not None and int(gols_c_ult) >= 1:
            mandante_fez_gol_ult = True
    except:
        pass
    valida_15 = (pct_15 >= 80 and mandante_fez_gol_ult)

    # Unders (Mínimo 4/5 >= 80%)
    valida_m45 = (pct_m45 >= 80)
    valida_m35 = (pct_m35 >= 80)
    valida_m55 = (pct_m55 >= 80)

    # Objeto dos unders para retorno rápido se necessário
    under_45_obj = {"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"} if valida_m45 else None
    under_35_obj = {"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"} if valida_m35 else None

    # ==========================================================
    # REGRA ABSOLUTA DO 0X0
    # ==========================================================
    if teve_zero_a_zero:
        if under_45_obj:
            return [under_45_obj]
        elif valida_m35:
            return [under_35_obj]
        # Se teve 0x0 mas não tem -4.5 nem -3.5, tenta o menor under disponível ou retorna vazio conforme sua regra
        return []

    # ==========================================================
    # APLICAÇÃO DA ORDEM DE PRIORIDADE ESTABELECIDA:
    # 1. +2.5
    # 2. +1.5
    # 3. -4.5
    # 4. -3.5
    # 5. +0.5 (desde que NÃO tenha -3.5 e nem -4.5 aprovados)
    # ==========================================================

    if valida_25:
        return [{"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"}]
    
    if valida_15:
        return [{"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"}]
    
    if valida_m45:
        return [under_45_obj]
    
    if valida_m35:
        return [under_35_obj]
    
    # +0.5 Gols (Exige >= 60% E que NÃO exista -3.5 ou -4.5 aprovados)
    sem_unders_fortes = not valida_m35 and not valida_m45
    if (pct_05 >= 60) and sem_unders_fortes:
        return [{"mercado": f"+0.5 Gols ({pct_05}%)", "tipo": "GOLS_05"}]

    # Se nenhum dos critérios acima bater, verifica se sobrou o -5.5 como última alternativa de under
    if pct_m55 >= 80:
        return [{"mercado": f"-5.5 Gols ({pct_m55}%)", "tipo": "GOLS_M55"}]

    return []
    
