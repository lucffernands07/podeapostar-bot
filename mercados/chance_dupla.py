            
    def verificar_chance_dupla(s):
    mercados = []
    
    # 1° VALIDAÇÃO: Trava unificada de Clean Sheet
    # Garante que os times não estão vindo de defesas que "fecham o jogo"
    casa_ok = s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_sofreu")
    
    # Se você quer que a Chance Dupla SÓ saia em jogos com tendência de gol:
    if not (casa_ok and fora_ok):
        return mercados

    # 2° Lógica 1X
    if s["casa_derrotas"] <= 1 and s["fora_derrotas"] >= 2:
        # Verifica se a casa não perdeu na última e o fora perdeu
        if s["casa_ult_res"] in ["V", "E"] and s["fora_ult_res"] == "D":
            pct = "100%" if s["casa_derrotas"] == 0 else "85%"
            mercados.append(f"1X ({pct})")
    
    # 3° Lógica 2X
    if s["fora_derrotas"] == 0 and s["casa_derrotas"] >= 2:
        if s["casa_ult_res"] == "D" and s["fora_ult_res"] in ["V", "E"]:
            mercados.append("2X (100%)")
            
    return mercados
