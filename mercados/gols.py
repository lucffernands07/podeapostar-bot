def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []
    
    # Validação para +1.5 Gols
    if ch15:
        if ch15 in ["70%", "85%"]:
            # REGRA RÍGIDA: Ambos precisam de +1.5 E ter sofrido gol (sem clean sheet)
            casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
            fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
            
            if casa_ok and fora_ok:
                resultados.append(f"🔶 Mercado: +1.5 Gols ({ch15})")
        else:
            # 100% (5/5 e 5/5) continua passando direto
            resultados.append(f"🔶 Mercado: +1.5 Gols ({ch15})")
            
    # Validação para +2.5 Gols
    if ch25:
        if ch25 in ["70%", "85%"]:
            # Mesma trava de segurança: ambos precisam ter sofrido gol e tido +1.5 no último
            casa_ok = s.get("casa_ult_15") and s.get("casa_ult_sofreu")
            fora_ok = s.get("fora_ult_15") and s.get("fora_ult_sofreu")
            
            if casa_ok and fora_ok:
                resultados.append(f"🔶 Mercado: +2.5 Gols ({ch25})")
        else:
            resultados.append(f"🔶 Mercado: +2.5 Gols ({ch25})")
            
    return resultados
    
