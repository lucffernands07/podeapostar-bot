def verificar_chance_dupla(s):
    # --- 1. REGRA DO CONFRONTO DIRETO (H2H) ---
    if s["h2h_jogos"] >= 6:
        sucesso_h2h_t1 = s["h2h_vitorias_t1"] + s["h2h_empates"]
        sucesso_h2h_t2 = s["h2h_vitorias_t2"] + s["h2h_empates"]
        
        if sucesso_h2h_t1 >= 4:
            pct = "100%" if sucesso_h2h_t1 == 6 else "85%" if sucesso_h2h_t1 == 5 else "70%"
            return [f"1X 🔥 ({pct})"]
            
        if sucesso_h2h_t2 >= 4:
            pct = "100%" if sucesso_h2h_t2 == 6 else "85%" if sucesso_h2h_t2 == 5 else "70%"
            return [f"2X 🔥 ({pct})"]
        
        # REMOVIDO: return [] (Para permitir que ele tente a regra padrão se o H2H não for fogo)

    # --- 2. SEGUNDA OPÇÃO (PADRÃO INDIVIDUAL) ---
    mercados = []
    sucesso_casa = s["casa_vitorias"] + s["casa_empates"]
    sucesso_fora = s["fora_vitorias"] + s["fora_empates"]

    if sucesso_casa >= 4:
        if s["fora_derrotas"] >= 2 or s["casa_ult_res"] == "V":
            pct = "100%" if sucesso_casa == 5 else "85%"
            mercados.append(f"1X ({pct})")
    
    elif sucesso_fora >= 4:
        if s["casa_derrotas"] >= 2 or s["fora_ult_res"] == "V":
            pct = "100%" if sucesso_fora == 5 else "90%"
            mercados.append(f"2X ({pct})")
            
    return mercados
    
