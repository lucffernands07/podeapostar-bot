def verificar_chance_dupla(s):
    mercados = []
    
    # --- 1. PRIORIDADE: CONFRONTO DIRETO (H2H) ---
    # Só analisa se houver 5 jogos registrados no H2H
    if s["h2h_jogos"] >= 5:
        sucesso_h2h_t1 = s["h2h_vitorias_t1"] + s["h2h_empates"]
        sucesso_h2h_t2 = s["h2h_vitorias_t2"] + s["h2h_empates"]
        
        # Critério: Mínimo 4/5 no confronto direto
        if sucesso_h2h_t1 >= 4:
            pct = "100%" if s["h2h_vitorias_t2"] == 0 else "90%"
            return [f"1X 🔥 ({pct})"] # Retorna imediato se achar H2H forte
            
        if sucesso_h2h_t2 >= 4:
            pct = "100%" if s["h2h_vitorias_t1"] == 0 else "90%"
            return [f"2X 🔥 ({pct})"] # Retorna imediato se achar H2H forte

    # --- 2. FALLBACK: PADRÃO ÚLTIMOS 5 JOGOS (CASA/FORA) ---
    # Se o H2H não atingiu 5 jogos ou não bateu 4/5, roda a lógica antiga
    sucesso_casa = s["casa_vitorias"] + s["casa_empates"]
    sucesso_fora = s["fora_vitorias"] + s["fora_empates"]

    # Lógica 1X Padrão
    if sucesso_casa >= 4: # Ajustado para 4/5 conforme sua regra geral
        if s["fora_derrotas"] >= 2 or s["casa_ult_res"] == "V":
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1X ({pct})")
    
    # Lógica 2X Padrão
    elif sucesso_fora >= 4:
        if s["casa_derrotas"] >= 2 or s["fora_ult_res"] == "V":
            pct = "100%" if s["fora_derrotas"] == 0 else "90%"
            mercados.append(f"2X ({pct})")
            
    return mercados
    
