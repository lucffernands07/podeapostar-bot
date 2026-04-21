def verificar_chance_dupla(s):
    mercados = []
    
    # REMOVEMOS A VALIDAÇÃO: if not (casa_ok and fora_ok)
    # Isso permite que o 1X apareça no México e em outros jogos favoritos

    # Lógica 1X: Baseada em derrotas e último resultado
    if s["casa_derrotas"] <= 1 and s["fora_derrotas"] >= 2:
        if s["casa_ult_res"] in ["V", "E"] and s["fora_ult_res"] == "D":
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1X ({pct})")
    
    # Lógica 2X
    if s["fora_derrotas"] == 0 and s["casa_derrotas"] >= 2:
        if s["casa_ult_res"] == "D" and s["fora_ult_res"] in ["V", "E"]:
            mercados.append("2X (100%)")
            
    return mercados
    
