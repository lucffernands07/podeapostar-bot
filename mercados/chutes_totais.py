"""
REGRAS DE MERCADO - CHUTES TOTAIS DO CONFRONTO / EQUIPE
"""

def verificar_chutes_totais(s):
    if not isinstance(s, dict):
        return []

    mercados_aprovados = []

    # Se a raspagem falhou ou não retornou dados
    if s.get("dados_incompletos_chutes", True):
        return []

    media_chutes_mandante = float(s.get("mandante_media_chutes_casa", 0) or 0)
    media_chutes_visitante = float(s.get("visitante_media_chutes_fora", 0) or 0)
    
    historico_mandante = s.get("chutes_mandante_h2h", [])
    historico_visitante = s.get("chutes_visitante_h2h", [])
    historico_total_jogo = s.get("chutes_jogo_total_h2h", [])

    media_total_jogo = media_chutes_mandante + media_chutes_visitante

    # 🟢 1. CHUTES TOTAIS DA PARTIDA (Ex: +18.5 Chutes no Jogo)
    if media_total_jogo >= 20.0:
        sucesso_total = sum(1 for x in historico_total_jogo if x >= 19)
        if sucesso_total >= 4:
            mercados_aprovados.append({
                "mercado": f"+18.5 Chutes Totais no Jogo",
                "tipo": "CHUTES_JOGO_185"
            })

    # 🟢 2. CHUTES TOTAIS POR EQUIPE
    if media_chutes_mandante >= 12.0:
        sucesso_m = sum(1 for x in historico_mandante if x >= 11)
        if sucesso_m >= 3:
            mercados_aprovados.append({
                "mercado": f"Mandante: +10.5 Chutes Totais",
                "tipo": "CHUTES_MANDANTE_105"
            })

    if media_chutes_visitante >= 10.0:
        sucesso_v = sum(1 for x in historico_visitante if x >= 9)
        if sucesso_v >= 3:
            mercados_aprovados.append({
                "mercado": f"Visitante: +8.5 Chutes Totais",
                "tipo": "CHUTES_VISITANTE_85"
            })

    return mercados_aprovados
          
