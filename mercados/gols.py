"""
REGRAS DE GOLS - VERSÃO COM EXCLUSÃO MÚTUA (OVER x UNDER) + FILTRO DE MÉDIA PARA +1.5 (60%)
Ordem de Prioridade e Exclusão:
- Se houver Over (+1.5 ou +2.5), os Unders são vetados.
- Se houver Under (-3.5 ou -4.5), os Overs são vetados.
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    if c < 2 or f < 2:
        return 0

    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    elif c >= 3 and f >= 3:
        return 60
    else:
        return 40


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # Recorrência dos times nos últimos 5 jogos
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))

    # Métricas de estatística
    m_feitos_casa = float(s.get("mandante_gols_feitos_casa", 0) or 0)
    m_sofridos_casa = float(s.get("mandante_gols_sofridos_casa", 0) or 0)
    v_feitos_fora = float(s.get("visitante_gols_feitos_fora", 0) or 0)
    v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)

    m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)
    v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)

    media_total_confronto = (m_feitos_casa + m_sofridos_casa + v_feitos_fora + v_sofridos_fora) / 5.0

    overs_aprovados = []
    unders_aprovados = []

    # Trava de risco contra goleadas
    visitante_peneira = v_sofridos_fora >= 7
    mandante_avassalador = m_feitos_casa >= 8
    pode_apostar_under = not (visitante_peneira or mandante_avassalador)

    # ==========================================================
    # AVALIAÇÃO DE OVERS (+1.5 e +2.5)
    # ==========================================================
    if pct_15 >= 80:
        # 80% ou 100% liberados diretamente pela consistência alta
        overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
    elif pct_15 == 60:
        # 60% agora exige a média combinada mínima de 2.4 para filtrar os jogos fracos
        if media_total_confronto >= 2.4:
            overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})

    if pct_25 >= 80:
        if media_total_confronto >= 2.4 and m_jogos_marcou_casa >= 4 and v_jogos_marcou_fora >= 4:
            overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (-4.5 e -3.5)
    # ==========================================================
    if pode_apostar_under and pct_m45 >= 60:
        if media_total_confronto <= 3.2:
            unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})

    if pode_apostar_under and pct_m35 >= 60:
        if media_total_confronto <= 2.6:
            unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})

    # ==========================================================
    # TRAVA DE EXCLUSÃO MÚTUA (NUNCA MISTURA OVER COM UNDER)
    # ==========================================================
    if overs_aprovados:
        return overs_aprovados
    else:
        return unders_aprovados
        
