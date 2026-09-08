"""
REGRAS DE GOLS - ATUALIZADO
- Over Geral: Mínimo 4/5 (>= 80%) para +1.5 e +2.5 (com regras específicas de resultado para o +2.5).
- Over +1.5: Exige estatística >= 80% E que o mandante tenha feito pelo menos 1 gol no último jogo em casa.
- Over +0.5: Exige no mínimo 3/5 (>= 60%).
- Regra de Exceção 0x0: Se o último jogo do mandante em casa ou visitante fora for 0x0, rebaixa para o -4.5.
- Under: Mínimo 4/5 (>= 80%), apenas o menor (-3.5 -> -4.5 -> -5.5).
- Regra de Ouro: Ou Over, ou Under (prioridade para Over).
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

    overs_aprovados = []
    unders_aprovados = []

    # ==========================================================
    # AVALIAÇÃO DE OVERS
    # ==========================================================
    
    # Validação da regra específica para o +2.5 Gols
    casa_25_qtd = int(s.get("casa_25", 0) or 0)
    fora_25_qtd = int(s.get("fora_25", 0) or 0)
    
    mandante_ok_25 = (casa_25_qtd >= 4) and (int(s.get("mandante_sem_derrota_casa", 0) or 0) >= 4)
    
    vis_vitorias = int(s.get("visitante_vitorias_fora", 0) or 0)
    vis_derrotas = int(s.get("visitante_derrotas_fora", 0) or 0)
    vis_empates = max(0, 5 - (vis_vitorias + vis_derrotas))
    visitante_ok_25 = (fora_25_qtd >= 4) and ((vis_derrotas + vis_empates) >= 4)

    if mandante_ok_25 and visitante_ok_25 and pct_25 >= 80:  
        overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # Validação da nova regra para o +1.5 Gols:
    # Exige percentual estatístico >= 80% E que o mandante tenha feito pelo menos 1 gol no último jogo em casa.
    # Como a raspagem armazena 't1_placar_1' (ex: "2-1"), podemos extrair o primeiro dígito ou usar gols_c_ult se disponível.
    mandante_fez_gol_ult = False
    try:
        # Tenta pegar o primeiro número do placar do último jogo em casa do mandante
        if placar_casa_ult and "-" in placar_casa_ult:
            gols_mandante_ult_partida = int(placar_casa_ult.split("-")[0])
            if gols_mandante_ult_partida >= 1:
                mandante_fez_gol_ult = True
        elif gols_c_ult is not None and int(gols_c_ult) >= 1:
            mandante_fez_gol_ult = True
    except:
        pass

    if pct_15 >= 80 and mandante_fez_gol_ult:
        overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
    
    # Over +0.5 exige no mínimo 3/5 (>= 60%)
    if pct_05 >= 60:  
        overs_aprovados.append({"mercado": f"+0.5 Gols ({pct_05}%)", "tipo": "GOLS_05"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (Apenas critério estatístico >= 80%)
    # ==========================================================
    if pct_m35 >= 80:
        unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
    if pct_m45 >= 80:
        unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})
    if pct_m55 >= 80:
        unders_aprovados.append({"mercado": f"-5.5 Gols ({pct_m55}%)", "tipo": "GOLS_M55"})

    # ==========================================================
    # APLICAÇÃO DAS REGRAS DE SELEÇÃO E CONVERSÃO DO 0x0
    # ==========================================================
    if overs_aprovados:
        escolha = overs_aprovados[0] # Pega o maior over
        
        # Se deu 1.5 ou 2.5 mas teve 0x0 recente, converte para o -4.5 (se o -4.5 estiver aprovado nos unders)
        if teve_zero_a_zero and escolha["tipo"] in ["GOLS_15", "GOLS_25"]:
            under_45 = next((item for item in unders_aprovados if item["tipo"] == "GOLS_M45"), None)
            if under_45:
                return [under_45]
                
        return [escolha]
    
    elif unders_aprovados:
        return [unders_aprovados[0]] # Pega o menor under (-3.5 > -4.5 > -5.5)
    
    return []
    
