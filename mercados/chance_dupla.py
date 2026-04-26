def verificar_chance_dupla(s):
    mercados = []
    
    # 1. Lógica 1X (Mandante precisa ter VENCIDO a última)
    if s["casa_derrotas"] <= 1 and s["casa_vitorias"] >= 2:
        if s["fora_derrotas"] >= 2:
            # RIGOR: Casa venceu (V) E Fora não venceu (D ou E)
            if s["casa_ult_res"] == "V" and s["fora_ult_res"] in ["D", "E"]:
                pct = "100%" if s["casa_derrotas"] == 0 else "90%"
                mercados.append(f"1X ({pct})")
    
    # 2. Lógica 2X (Visitante precisa ter VENCIDO a última)
    if s["fora_derrotas"] <= 1 and s["fora_vitorias"] >= 2:
        if s["casa_derrotas"] >= 2:
            # RIGOR: Fora venceu (V) E Casa perdeu (D)
            # Para o 2X ser seguro, o mandante tem que estar em crise real
            if s["fora_ult_res"] == "V" and s["casa_ult_res"] == "D":
                pct = "100%" if s["fora_derrotas"] == 0 else "90%"
                mercados.append(f"2X ({pct})")
            
    return mercados
    
