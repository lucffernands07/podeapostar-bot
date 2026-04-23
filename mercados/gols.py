def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    # 1. Trava Mestra: Se houve Clean Sheet (0 no placar) no jogo 1, para tudo.
    if s.get("pular_gols"):
        return []

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []

    # 2. Filtro de Recorrência: Ambos devem ter sofrido gol e tido +1.5 no jogo mais recente
    casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
    fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
    
    if not (casa_ok and fora_ok):
        return resultados

    # 3. Se passou em tudo, gera o mercado com a dica
    if ch15:
        # O Clean Sheet protege tanto o +1.5 quanto o -4.5 de jogos 0x0 ou 1x0
        resultados.append(f"+1.5 Gols ({ch15}) | Dica: -4.5")
            
    if ch25:
        resultados.append(f"+2.5 Gols ({ch25})")
            
    return resultados
    
