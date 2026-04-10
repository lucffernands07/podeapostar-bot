def verificar_chance_dupla(s):
    mercados = []
    
    # Lógica 1X
    if s["casa_derrotas"] <= 1 and s["fora_derrotas"] >= 2:
        if s["casa_ult_res"] in ["V", "E"] and s["fora_ult_res"] == "D":
            # Se a casa estiver invicta (0 derrotas), 100%, se tiver 1 derrota, 85%
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1x ({pct})")
    
    # Lógica 2X
    if s["fora_derrotas"] == 0 and s["casa_derrotas"] >= 2:
        if s["casa_ult_res"] == "D":
            mercados.append("2x (100%)") # 2X só entra se o visitante estiver invicto
            
    return mercados
