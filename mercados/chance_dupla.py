def verificar_chance_dupla(s):
    mercados = []
    
    # 1. Filtro de gols REMOVIDO conforme solicitado.
    # Agora a análise foca apenas no desempenho de resultados.

    # 2° Lógica 1X (Mantida conforme padrão anterior)
    if s["casa_derrotas"] <= 1 and s["fora_derrotas"] >= 2:
        if s["casa_ult_res"] in ["V", "E"] and s["fora_ult_res"] == "D":
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1X ({pct})")
    
    # 3° Lógica 2X (AJUSTADA)
    # Regra 2: Time de fora com no máximo 1 derrota
    if s["fora_derrotas"] <= 1 and s["casa_derrotas"] >= 2:
        # Regra 3: Último resultado do time de fora deve ser SOMENTE VITÓRIA
        # E o time da casa deve ter perdido na última
        if s["casa_ult_res"] == "D" and s["fora_ult_res"] == "V":
            # Define porcentagem: 100% se for invicto, 85% se tiver 1 derrota
            pct = "100%" if s["fora_derrotas"] == 0 else "85%"
            mercados.append(f"2X ({pct})")
            
    return mercados
    
