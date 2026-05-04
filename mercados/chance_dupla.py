def verificar_chance_dupla(s):
    mercados = []
    
    # --- REGRA 1X ---
    # Passo 1: Casa venceu a última e Fora empatou ou perdeu
    # No seu main a chave é 'casa_ult_res' e 'fora_ult_res'
    condicao_individual_1x = (s.get("casa_ult_res") == "V" and s.get("fora_ult_res") in ["E", "D"])
    
    # Passo 2: No H2H, o mandante (t1) não perdeu (V ou E)
    # O seu main usa h2h_vitorias_t2 para saber se o visitante venceu o mandante
    condicao_h2h_1x = (s.get("h2h_vitorias_t2", 0) == 0)

    if condicao_individual_1x and condicao_h2h_1x:
        pct = "100%" if s.get("casa_vitorias", 0) >= 4 else "85%"
        mercados.append(f"1X ({pct})")
    
    # --- REGRA 2X ---
    # Passo 1: Fora venceu a última e Casa empatou ou perdeu
    condicao_individual_2x = (s.get("fora_ult_res") == "V" and s.get("casa_ult_res") in ["E", "D"])
    
    # Passo 2: Visitante não perdeu no H2H (t1 não venceu)
    condicao_h2h_2x = (s.get("h2h_vitorias_t1", 0) == 0)

    if condicao_individual_2x and condicao_h2h_2x:
        pct = "100%" if s.get("fora_vitorias", 0) >= 4 else "90%"
        mercados.append(f"2X ({pct})")
            
    return mercados
    
