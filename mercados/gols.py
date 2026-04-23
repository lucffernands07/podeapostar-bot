def calcular_chance(c, f):
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    # 1. Trava Mestra (Agora baseada em Total <= 1 no jogo da CASA)
    travado_casa = s.get("pular_gols", False) 

    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # Recorrência: Agora só exige que o último jogo da CASA tenha tido +1.5 gols.
    # Removemos a exigência de "ter sofrido gol" e a trava do time de fora.
    casa_ok = s.get("casa_ult_15") 
    
    # --- MERCADO +1.5 GOLS ---
    # Só entra se a CASA não estiver travada (0x0/1x0) e teve +1.5 no último jogo
    if ch15 and not travado_casa and casa_ok:
        resultados.append(f"+1.5 Gols ({ch15})")

    # --- LÓGICA DE EXCLUSÃO INTELIGENTE ---
    # Se o jogo for bom para +2.5, priorizamos ele.
    if ch25 and not travado_casa and casa_ok:
        resultados.append(f"+2.5 Gols ({ch25})")
    
    # Se NÃO for +2.5, tentamos o -4.5 de segurança (Totalmente independente de travas)
    elif ch45:
        resultados.append(f"-4.5 Gols ({ch45})")
            
    return resultados
    
