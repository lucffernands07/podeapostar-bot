def verificar_chance_dupla(s):
    # --- 1. REGRA DO CONFRONTO DIRETO (H2H) ---
    # Se existirem 5 jogos ou mais no histórico direto
    if s["h2h_jogos"] >= 5:
        sucesso_h2h_t1 = s["h2h_vitorias_t1"] + s["h2h_empates"]
        sucesso_h2h_t2 = s["h2h_vitorias_t2"] + s["h2h_empates"]
        
        # Se bater 4/5, envia com fogo 🔥
        if sucesso_h2h_t1 >= 4:
            pct = "100%" if s["h2h_vitorias_t2"] == 0 else "90%"
            return [f"1X 🔥 ({pct})"]
            
        if sucesso_h2h_t2 >= 4:
            pct = "100%" if s["h2h_vitorias_t1"] == 0 else "90%"
            return [f"2X 🔥 ({pct})"]
        
        # Se tem 5 jogos mas NÃO bateu 4/5, DESCARTA (não tenta a segunda opção)
        return []

    # --- 2. SEGUNDA OPÇÃO (SÓ SE O H2H TIVER MENOS DE 5 JOGOS) ---
    mercados = []
    sucesso_casa = s["casa_vitorias"] + s["casa_empates"]
    sucesso_fora = s["fora_vitorias"] + s["fora_empates"]

    # Regra 1X Padrão (Mínimo 4/5 individual)
    if sucesso_casa >= 4:
        if s["fora_derrotas"] >= 2 or s["casa_ult_res"] == "V":
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1X ({pct})")
    
    # Regra 2X Padrão (Mínimo 4/5 individual)
    elif sucesso_fora >= 4:
        if s["casa_derrotas"] >= 2 or s["fora_ult_res"] == "V":
            pct = "100%" if s["fora_derrotas"] == 0 else "90%"
            mercados.append(f"2X ({pct})")
            
    return mercados
    
