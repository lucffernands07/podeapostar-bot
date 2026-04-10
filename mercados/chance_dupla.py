def verificar_chance_dupla(s):
    """
    Mantém a lógica de análise de força baseada no histórico de 5 jogos.
    """
    mercados = []
    
    # Lógica 1X (Casa)
    # Se a casa tem poucas derrotas (0 ou 1) e o visitante tem muitas (2 ou mais)
    if s["casa_derrotas"] <= 1 and s["fora_derrotas"] >= 2:
        # Reforça com a tendência do último jogo
        if s["casa_ult_res"] in ["V", "E"] and s["fora_ult_res"] == "D":
            mercados.append("1x")
    
    # Lógica 2X (Fora)
    # Se o visitante está invicto (0 derrotas) e a casa está perdendo (2 ou mais)
    if s["fora_derrotas"] == 0 and s["casa_derrotas"] >= 2:
        if s["casa_ult_res"] == "D":
            mercados.append("2x")
            
    return mercados
