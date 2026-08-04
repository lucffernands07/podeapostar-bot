"""
REGRAS DE MERCADO - CHUTES TOTAIS DO JOGO (ALINHADO À BETANO)
Soma das médias dos últimos 5 jogos -> Linha de Segurança (+22.5 / +23.5 / +24.5)
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

    # 2. Define a Linha de Aposta com base na Média Esperada
    # Criamos margem de segurança para buscar odds interessantes (~1.40 - 1.60 na Betano)
    if media_esperada >= 27.0:
        linha_sugerida = "+24.5 Chutes Totais no Jogo"
    elif media_esperada >= 25.0:
        linha_sugerida = "+22.5 Chutes Totais no Jogo"
    elif media_esperada >= 23.0:
        linha_sugerida = "+20.5 Chutes Totais no Jogo"
    else:
        # Se a média somada for menor que 23 chutes, não vale o risco
        return []

    mercados_aprovados.append({
        "mercado": f"{linha_sugerida} (Média: {media_esperada:.1f})",
        "tipo": "CHUTES_JOGO_TOTAL"
    })

    return mercados_aprovados
