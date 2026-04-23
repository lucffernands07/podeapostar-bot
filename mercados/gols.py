def verificar_gols(s):
    # 1. Trava Mestra (Afeta APENAS o +1.5 e +2.5)
    travado = s.get("pular_gols", False)

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # Filtros de Recorrência (Usados apenas para o mercado de OVER)
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
    
    # --- MERCADO +1.5 GOLS ---
    if ch15 and not travado and (casa_ok and fora_ok):
        resultados.append(f"+1.5 Gols ({ch15})")

    # --- LÓGICA DE EXCLUSÃO INTELIGENTE ---
    # Primeiro checamos o +2.5
    if ch25 and not travado and (casa_ok and fora_ok):
        resultados.append(f"+2.5 Gols ({ch25})")
    
    # O -4.5 só entra se o +2.5 NÃO tiver sido adicionado
    elif ch45:
        resultados.append(f"-4.5 Gols ({ch45})")
            
    return resultados
