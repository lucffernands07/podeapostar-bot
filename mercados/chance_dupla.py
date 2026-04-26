def verificar_chance_dupla(s):
    mercados = []
    
    # Sucesso nos últimos 5 jogos (Vitórias + Empates)
    sucesso_casa = s["casa_vitorias"] + s["casa_empates"]
    sucesso_fora = s["fora_vitorias"] + s["fora_empates"]

    # --- LÓGICA 1X (MAIS FLEXÍVEL - MANDANTE) ---
    # 1. Mínimo 3/5 de aproveitamento
    if sucesso_casa >= 3:
        # 2. Adversário precisa ter pelo menos 2 derrotas nos últimos 5
        if s["fora_derrotas"] >= 2:
            # 3. FILTRO DE MOMENTO SECO: Vitória do favorito E Derrota do adversário
            if s["casa_ult_res"] == "V" and s["fora_ult_res"] == "D":
                pct = "100%" if s["casa_derrotas"] == 0 else "85%"
                mercados.append(f"1X ({pct})")
    
    # --- LÓGICA 2X (MAIS RÍGIDA - VISITANTE) ---
    # 1. MÍNIMO 4/5 de aproveitamento (Visitante precisa ser muito sólido)
    if sucesso_fora >= 4:
        # 2. Adversário (Mandante) precisa estar mal (min 2 derrotas)
        if s["casa_derrotas"] >= 2:
            # 3. FILTRO DE MOMENTO SECO: Vitória do favorito E Derrota do adversário
            if s["fora_ult_res"] == "V" and s["casa_ult_res"] == "D":
                pct = "100%" if s["fora_derrotas"] == 0 else "90%"
                mercados.append(f"2X ({pct})")
            
    return mercados
    
