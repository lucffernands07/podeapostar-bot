"""
REGRAS DE MERCADO - GOLS
1. Prioridade Máxima: -4.5 Gols se o jogo for estatisticamente "Under".
2. Over 1.5/2.5: Requer sucesso de pelo menos 3/5 nas últimas 5 partidas (com escala de confiança).
3. Filtro de Segurança: Evita sugerir Over e Under no mesmo jogo.
4. Coerência: Máximo de um jogo com +2.5 Gols por bilhete (regra aplicada no main.py).
"""

def calcular_chance(c, f):
    """
    Calcula a porcentagem de confiança baseada na recorrência 
    dos últimos 5 jogos da CASA (c) e do FORA (f).
    """
    # Filtro 5 de 5 (Máxima Confiança)
    if c == 5 and f == 5: 
        return "100%"
    
    # Filtro 4 de 5 (Alta Confiança)
    if (c >= 4 and f >= 5) or (c >= 5 and f >= 4) or (c == 4 and f == 4): 
        return "85%"
    
    # Filtro 3 de 5 (Confiança Mínima / Backup)
    if (c >= 3 and f >= 3):
        return "70%"
    
    return None

def verificar_gols(s):
    """
    Analisa os mercados de gols com base nas estatísticas brutas fornecidas.
    's' é o dicionário de estatísticas vindo do main.py.
    """
    # 1. Cálculos de probabilidade para cada mercado
    ch15 = calcular_chance(s.get("casa_15", 0), s.get("fora_15", 0))
    ch25 = calcular_chance(s.get("casa_25", 0), s.get("fora_25", 0))
    
    # Para o mercado de -4.5, buscamos a recorrência de jogos que terminaram UNDER
    ch45_under = calcular_chance(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    
    resultados = []

    # --- LÓGICA DE PRIORIDADE E EXCLUSÃO ---

    # 1ª PRIORIDADE: SEGURANÇA (-4.5 Gols)
    # Se o jogo for estatisticamente Under (-4.5) e não tiver força para Over 1.5
    if ch45_under and not ch15:
        resultados.append({
            "mercado": "-4.5 Gols",
            "confianca": ch45_under,
            "tipo": "UNDER"
        })
        # Retorna imediatamente para manter a coerência (não sugerir Over no mesmo jogo)
        return resultados

    # 2ª PRIORIDADE: TENDÊNCIA DE OVER (+1.5 Gols)
    if ch15:
        resultados.append({
            "mercado": "+1.5 Gols",
            "confianca": ch15,
            "tipo": "OVER_15"
        })
    
    # 3ª PRIORIDADE: TENDÊNCIA DE OVER ALTO (+2.5 Gols)
    if ch25:
        resultados.append({
            "mercado": "+2.5 Gols",
            "confianca": ch25,
            "tipo": "OVER_25"
        })

    return resultados
    
