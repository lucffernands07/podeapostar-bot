"""
REGRAS DE MERCADO - CHUTES TOTAIS DO JOGO (FLEXÍVEL: OVER E UNDER)
Soma das médias dos últimos 5 jogos -> Sugere linha Over ou Under proporcional.
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    # Lê as médias já calculadas pelo scraper dos últimos 5 jogos
    media_m = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_v = float(s.get("visitante_media_chutes_fora", 0) or 0)

    # Se não houver dados raspados o suficiente, ignora
    if media_m == 0 or media_v == 0:
        return []

    # 1. Soma das Médias (Mandante em casa + Visitante fora)
    media_esperada = media_m + media_v

    mercados_aprovados = []

    # 2. Define dinamicamente a linha de Over ou Under com base na média somada
    if media_esperada >= 27.0:
        linha_sugerida = "+24.5 Chutes Totais no Jogo"
        tipo_mercado = "CHUTES_JOGO_OVER"
    elif media_esperada >= 24.0:
        linha_sugerida = "+21.5 Chutes Totais no Jogo"
        tipo_mercado = "CHUTES_JOGO_OVER"
    elif media_esperada >= 21.0:
        # Média intermediária/equilibrada
        linha_sugerida = "+19.5 Chutes Totais no Jogo"
        tipo_mercado = "CHUTES_JOGO_OVER"
    elif media_esperada <= 16.0:
        # Times que finalizam muito pouco: excelente para explorar o Under na Betano!
        linha_sugerida = "-21.5 Chutes Totais no Jogo"
        tipo_mercado = "CHUTES_JOGO_UNDER"
    else:
        # Faixa neutra onde a média fica entre 16 e 21
        linha_sugerida = "-23.5 Chutes Totais no Jogo"
        tipo_mercado = "CHUTES_JOGO_UNDER"

    mercados_aprovados.append({
        "mercado": f"{linha_sugerida} (Média: {media_esperada:.1f})",
        "tipo": tipo_mercado
    })

    return mercados_aprovados
    
