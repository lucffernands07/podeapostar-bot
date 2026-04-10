def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []
    if ch15: resultados.append(f"🎯 Mercado: +1.5 Gols ({ch15})")
    if ch25: resultados.append(f"🎯 Mercado: +2.5 Gols ({ch25})")
    return resultados
  
