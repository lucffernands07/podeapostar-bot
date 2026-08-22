"""
REGRAS DE MERCADO - CHUTES SEPARADOS POR TIME (FORMATO DECIMAL LIVRE)
Retorna a média isolada de chutes de cada time (mandante em casa / visitante fora).
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    # Lê as médias já calculadas pelo scraper dos últimos 5 jogos
    media_m = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_v = float(s.get("visitante_media_chutes_fora", 0) or 0)

    mercados_aprovados = []

    # Se houver média do mandante, retorna separadamente
    if media_m > 0:
        mercados_aprovados.append({
            "mercado": f"Chutes do Mandante: {media_m:.1f}",
            "tipo": "CHUTES_MANDANTE"
        })

    # Se houver média do visitante, retorna separadamente
    if media_v > 0:
        mercados_aprovados.append({
            "mercado": f"Chutes do Visitante: {media_v:.1f}",
            "tipo": "CHUTES_VISITANTE"
        })

    return mercados_aprovados
    
