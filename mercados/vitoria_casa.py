def verificar_vitoria_casa(s):
    """
    REGRA DE SEGURANÇA MÁXIMA - VITÓRIA CASA
    Passo 1: Momento Imediato (Último jogo individual).
    Passo 2: Tabu no Confronto Direto (2 últimos jogos H2H).
    """
    
    # --- PASSO 1: MOMENTO IMEDIATO ---
    # t1_resultado_1: último resultado do mandante (V/E/D)
    # t2_resultado_1: último resultado do visitante (V/E/D)
    casa_ultimo = s.get("t1_resultado_1", "").upper()
    fora_ultimo = s.get("t2_resultado_1", "").upper()
    
    # Regra: Casa deve vir de VITÓRIA. Fora deve vir de EMPATE ou DERROTA.
    valida_momento = (casa_ultimo == "V") and (fora_ultimo in ["E", "D"])
    
    if not valida_momento:
        return [] # Se o momento não bate, já descarta aqui

    # --- PASSO 2: CONFRONTO DIRETO (2 ÚLTIMOS JOGOS) ---
    # h2h_res_1: Resultado mais recente entre eles
    # h2h_res_2: Segundo resultado mais recente
    # Nota: Assumindo que 'V' no H2H significa vitória do Time 1 (Mandante)
    h2h_1 = s.get("h2h_res_1", "").upper()
    h2h_2 = s.get("h2h_res_2", "").upper()
    
    ultimos_dois_h2h = [h2h_1, h2h_2]
    
    # Regra: Pelo menos 1 vitória e NENHUMA derrota nos últimos 2 jogos
    tem_vitoria_h2h = "V" in ultimos_dois_h2h
    tem_derrota_h2h = "D" in ultimos_dois_h2h
    
    if tem_vitoria_h2h and not tem_derrota_h2h:
        # Se passou pelos dois filtros, calculamos a confiança
        # Se os dois últimos H2H foram vitória, 100%. Se foi 1V e 1E, 80%.
        if h2h_1 == "V" and h2h_2 == "V":
            pct = "100%"
        else:
            pct = "80%"
            
        return [f"Vitória Casa 💎 ({pct})"]

    return []
    
