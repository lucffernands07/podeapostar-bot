def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    # --- NOVA TRAVA AQUI ---
    # Se a main detectou Clean Sheet, ela marca pular_gols como True.
    # Se estiver True, retornamos a lista vazia imediatamente.
    if s.get("pular_gols"):
        return []
    # -----------------------

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []

    # 1° VALIDAÇÃO: Clean sheet para TODOS (70, 85 ou 100%)
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
    
    if not (casa_ok and fora_ok):
        return resultados

    # 2° SELEÇÃO: Se passou na trava, verifica as chances
    if ch15:
        resultados.append(f"+1.5 Gols ({ch15})")
            
    if ch25:
        resultados.append(f"+2.5 Gols ({ch25})")
            
    return resultados
