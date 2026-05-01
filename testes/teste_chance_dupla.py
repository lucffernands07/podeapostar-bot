def verificar_chance_dupla(s):
    sugestoes = []
    
    # Resultados do último jogo individual (V, E ou D)
    casa_ult = s.get("casa_ult_res", "") 
    fora_ult = s.get("fora_ult_res", "") 
    
    # No seu dicionário 's', as vitórias do Time 2 (H2H) representam derrotas do Time 1 (Casa)
    # e vitórias do Time 1 representam derrotas do Time 2 (Fora).
    
    # --- REGRA 1X ---
    # Casa venceu a última, Fora perdeu a última.
    # H2H: Casa não pode ter perdido os últimos confrontos (vitorias_t2 deve ser 0)
    if casa_ult == "V" and fora_ult == "D":
        if s.get("h2h_vitorias_t2", 0) == 0:
            # Se a casa domina o H2H (venceu 2 ou mais), 85%. Se empatou muito, 70%.
            pct = "85%" if s.get("h2h_vitorias_t1", 0) >= 2 else "70%"
            sugestoes.append(f"1X 🔥 ({pct})")

    # --- REGRA 2X ---
    # Fora venceu a última, Casa perdeu a última.
    # H2H: Fora não pode ter perdido os últimos confrontos (vitorias_t1 deve ser 0)
    if fora_ult == "V" and casa_ult == "D":
        if s.get("h2h_vitorias_t1", 0) == 0:
            pct = "85%" if s.get("h2h_vitorias_t2", 0) >= 2 else "70%"
            sugestoes.append(f"2X 🔥 ({pct})")

    return sugestoes
