"""
REGRAS DE MERCADO - CHUTES TOTAIS DO CONFRONTO / EQUIPE
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    mercados_aprovados = []

    # Métricas e Históricos do dicionário s
    media_chutes_mandante = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_chutes_visitante = float(s.get("visitante_media_chutes_fora", 0) or 0)
    
    historico_mandante = s.get("chutes_mandante_h2h", [])
    historico_visitante = s.get("chutes_visitante_h2h", [])
    historico_total_jogo = s.get("chutes_jogo_total_h2h", [])

    media_total_jogo = media_chutes_mandante + media_chutes_visitante

    # Se não capturou histórico suficiente, encerra
    if not historico_mandante and not historico_visitante and not historico_total_jogo:
        return []

    # 🟢 1. CHUTES TOTAIS DA PARTIDA (Média >= 17.0)
    if media_total_jogo >= 17.0:
        sucesso_total = sum(1 for x in historico_total_jogo if x >= 16)
        if sucesso_total >= 3:
            mercados_aprovados.append({
                "mercado": f"+16.5 Chutes Totais no Jogo",
                "tipo": "CHUTES_JOGO_165"
            })

    # 🟢 2. CHUTES TOTAIS MANDANTE (Média >= 10.0)
    if media_chutes_mandante >= 10.0:
        sucesso_m = sum(1 for x in historico_mandante if x >= 9)
        if sucesso_m >= 3:
            mercados_aprovados.append({
                "mercado": f"Mandante: +9.5 Finalizações",
                "tipo": "CHUTES_MANDANTE_95"
            })

    # 🟢 3. CHUTES TOTAIS VISITANTE (Média >= 8.0)
    if media_chutes_visitante >= 8.0:
        sucesso_v = sum(1 for x in historico_visitante if x >= 7)
        if sucesso_v >= 3:
            mercados_aprovados.append({
                "mercado": f"Visitante: +7.5 Finalizações",
                "tipo": "CHUTES_VISITANTE_75"
            })

    return mercados_aprovados
    
