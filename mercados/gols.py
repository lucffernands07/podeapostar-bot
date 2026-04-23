def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    # 1. Trava Mestra (Afeta +1.5 e +2.5)
    travado = s.get("pular_gols", False)

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    # 2. Estatística própria para o -4.5 (Sem trava de Clean Sheet conforme pedido)
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # Filtros de Recorrência para o mercado de OVER
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
    
    # 3. Lógica do Bilhete
    if ch15 and not travado and (casa_ok and fora_ok):
        texto = f"+1.5 Gols ({ch15})"
        
        # Adiciona a dica apenas se o -4.5 também passar na regra de 4/5 ou 5/5
        if ch45:
            texto += f" | Dica: -4.5 ({ch45})"
            
        resultados.append(texto)
            
    if ch25 and not travado and (casa_ok and fora_ok):
        resultados.append(f"+2.5 Gols ({ch25})")
            
    return resultados
    
