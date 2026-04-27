def verificar_chance_dupla(s):
    # --- 1. REGRA DO CONFRONTO DIRETO (H2H) - AGORA 4/6 ---
    if s["h2h_jogos"] >= 6:
        sucesso_h2h_t1 = s["h2h_vitorias_t1"] + s["h2h_empates"]
        sucesso_h2h_t2 = s["h2h_vitorias_t2"] + s["h2h_empates"]
        
        # LÓGICA PARA TIME DA CASA (1X)
        if sucesso_h2h_t1 >= 4:
            if sucesso_h2h_t1 == 6: pct = "100%"
            elif sucesso_h2h_t1 == 5: pct = "85%"
            else: pct = "70%" # Para 4/6
            return [f"1X 🔥 ({pct})"]
            
        # LÓGICA PARA TIME DE FORA (2X)
        if sucesso_h2h_t2 >= 4:
            if sucesso_h2h_t2 == 6: pct = "100%"
            elif sucesso_h2h_t2 == 5: pct = "85%"
            else: pct = "70%" # Para 4/6
            return [f"2X 🔥 ({pct})"]
        
        # Se tem 6 jogos mas não bateu 4/6, descarta o mercado
        return []

    # --- 2. SEGUNDA OPÇÃO (SÓ SE O H2H TIVER 5 JOGOS OU MENOS) ---
    mercados = []
    sucesso_casa = s["casa_vitorias"] + s["casa_empates"]
    sucesso_fora = s["fora_vitorias"] + s["fora_empates"]

    # Regra 1X Padrão (Mínimo 4/5 individual)
    if sucesso_casa >= 4:
        if s["fora_derrotas"] >= 2 or s["casa_ult_res"] == "V":
            # 5/5 vira 100%, 4/5 vira 85% (seguindo sua lógica padrão)
            pct = "100%" if sucesso_casa == 5 else "85%"
            mercados.append(f"1X ({pct})")
    
    # Regra 2X Padrão (Mínimo 4/5 individual)
    elif sucesso_fora >= 4:
        if s["casa_derrotas"] >= 2 or s["fora_ult_res"] == "V":
            pct = "100%" if sucesso_fora == 5 else "90%"
            mercados.append(f"2X ({pct})")
            
    return mercados
    
