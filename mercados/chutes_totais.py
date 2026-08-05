"""
REGRAS DE MERCADO - CHUTES TOTAIS DO Jogo (FORMATO DECIMAL LIVRE)
Retorna a média esperada calculada dos últimos 5 jogos para livre escolha na Betano.
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    # Lê as médias já calculadas pelo scraper dos últimos 5 jogos (CASA para o mandante / FORA para o visitante)
    media_m = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_v = float(s.get("visitante_media_chutes_fora", 0) or 0)

    # Se não houver dados raspados o suficiente, ignora
    if media_m == 0 or media_v == 0:
        return []

    # 1. Soma das Médias (Mandante em casa + Visitante fora)
    media_esperada = media_m + media_v

    mercados_aprovados = []

    # 2. Retorna a média exata e limpa, mantendo a chave padrão CHUTES_JOGO_TOTAL
    mercados_aprovados.append({
        "mercado": f"Chutes Totais no Jogo: {media_esperada:.1f}",
        "tipo": "CHUTES_JOGO_TOTAL"
    })

    return mercados_aprovados
    
