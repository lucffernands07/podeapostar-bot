def verificar_gols(s):
    # 1. Trava Mestra (Agora aplicada de forma seletiva)
    travado_casa = s.get("pular_gols", False) # True se o jogo 1 da CASA foi 0x0 ou 1x0

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # Filtros de Recorrência (Ajustados conforme seu pedido)
    # Note que removemos a trava do time de fora nas condições
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    
    # --- MERCADO +1.5 GOLS ---
    # Agora só checa se a CASA está travada e se a CASA passou na recorrência
    if ch15 and not travado_casa and casa_ok:
        resultados.append(f"+1.5 Gols ({ch15})")

    # --- LÓGICA DE EXCLUSÃO INTELIGENTE ---
    # +2.5 também só depende da trava e recorrência da CASA
    if ch25 and not travado_casa and casa_ok:
        resultados.append(f"+2.5 Gols ({ch25})")
    
    # O -4.5 continua independente (entra se o +2.5 não entrar)
    elif ch45:
        resultados.append(f"-4.5 Gols ({ch45})")
            
    return resultados
