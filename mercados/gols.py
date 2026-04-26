"""
REGRAS DE MERCADO - GOLS
1. Prioridade Máxima: -4.5 Gols se o jogo for estatisticamente "Under" (Sem tendência de Over).
2. Over 1.5/2.5: Ativado apenas se a recorrência combinada for de 4/5 (70%) ou 5/5 (85%-100%).
3. Filtro de Segurança: Evita sugerir Over e Under no mesmo jogo para manter a coerência do bilhete.
4. Independência: Não utiliza travas manuais do último jogo, focando na média estatística dos últimos 5.
"""

def calcular_chance(c, f):
    """
    Calcula a porcentagem de confiança baseada na recorrência 
    dos últimos 5 jogos da CASA (c) e do FORA (f).
    """
    if c == 5 and f == 5: return "100%"
    if (c == 5 and f == 4) or (c == 4 and f == 5): return "85%"
    if c == 4 and f == 4: return "70%"
    return None

def verificar_gols(s):
    """
    Analisa os mercados de gols com base nas estatísticas brutas fornecidas pelo main.py.
    """
    # 1. Cálculos de probabilidade (Mínimo 4/5 para validar)
    ch15 = calcular_chance(s["casa_15"], s["fora_15"])
    ch25 = calcular_chance(s["casa_25"], s["fora_25"])
    ch45 = calcular_chance(s.get("casa_45", 0), s.get("fora_45", 0))
    
    resultados = []

    # --- LÓGICA DE PRIORIDADE E EXCLUSÃO ---

    # 1ª PRIORIDADE: SEGURANÇA (-4.5 Gols)
    # Se o jogo for muito seguro para Under e NÃO atingir o critério de Over
    if ch45 and not ch15 and not ch25:
        resultados.append(f"-4.5 Gols ({ch45})")
        # Retorna imediatamente para o -4.5 ser a única sugestão de gols deste jogo
        return resultados

    # 2ª PRIORIDADE: TENDÊNCIA DE OVER (+1.5 Gols)
    if ch15:
        resultados.append(f"+1.5 Gols ({ch15})")
    
    # 3ª PRIORIDADE: TENDÊNCIA DE OVER ALTO (+2.5 Gols)
    if ch25:
        resultados.append(f"+2.5 Gols ({ch25})")

    return resultados
    
