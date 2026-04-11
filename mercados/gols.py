def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    
    resultados = []
    
    # Ajuste para +1.5 Gols
    if ch15:
        if ch15 == "70%":
            # TRAVA: Só aceita 70% se o último jogo de um dos dois foi +1.5
            if s.get("casa_ult_15") or s.get("fora_ult_15"):
                resultados.append(f"🔶 Mercado: +1.5 Gols ({ch15})")
        else:
            # 85% e 100% passam direto
            resultados.append(f"🔶 Mercado: +1.5 Gols ({ch15})")
            
    # Ajuste para +2.5 Gols (mesma lógica de segurança)
    if ch25:
        if ch25 == "70%":
            if s.get("casa_ult_25") or s.get("fora_ult_25"):
                resultados.append(f"🔶 Mercado: +2.5 Gols ({ch25})")
        else:
            resultados.append(f"🔶 Mercado: +2.5 Gols ({ch25})")
            
    return resultados
