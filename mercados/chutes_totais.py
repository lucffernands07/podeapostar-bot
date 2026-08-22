"""
REGRAS DE MERCADO - FINALIZAÇÕES TOTAIS SEPARADAS POR TIME (SUPERSCORE)
Retorna a média isolada de finalizações de cada time com base na aba de estatísticas.
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    # Lê as médias puxadas diretamente da aba de estatísticas do Superscore
    media_m = float(s.get("media_finalizacoes_mandante", 0) or 0)
    media_v = float(s.get("media_finalizacoes_visitante", 0) or 0)

    mercados_aprovados = []

    # Se houver média do mandante, retorna separadamente
    if media_m > 0:
        mercados_aprovados.append({
            "mercado": f"Finalizações do Mandante: {media_m:.1f}",
            "tipo": "CHUTES_MANDANTE"
        })

    # Se houver média do visitante, retorna separadamente
    if media_v > 0:
        mercados_aprovados.append({
            "mercado": f"Finalizações do Visitante: {media_v:.1f}",
            "tipo": "CHUTES_VISITANTE"
        })

    return mercados_aprovados
