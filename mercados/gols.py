def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    # 1. Trava Mestra (Afeta APENAS o +1.5 e +2.5)
    travado = s.get("pular_gols", False)

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    # 2. Estatística para o -4.5 (Independente e com o nome corrigido)
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # Filtros de Recorrência (Usados apenas para o mercado de OVER)
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
    
    # --- MERCADO +1.5 GOLS ---
    if ch15 and not travado and (casa_ok and fora_ok):
        resultados.append(f"+1.5 Gols ({ch15})")

    # --- MERCADO -4.5 GOLS (SEPARADO E INDEPENDENTE) ---
    if ch45:
        resultados.append(f"-4.5 Gols ({ch45})") # <-- Nome corrigido para -4.5
            
    # --- MERCADO +2.5 GOLS ---
    if ch25 and not travado and (casa_ok and fora_ok):
        resultados.append(f"+2.5 Gols ({ch25})")
            
    return resultados
    
