"""
REGRAS DE GOLS - VERSÃO CORRIGIDA E EQUILIBRADA
- Mantém travas anti-goleada no Under
- Libera +1.5 Gols para médias coerentes (>= 1.8 ou 2.0)
- Sem funções duplicadas
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    if c < 3 or f < 3:
        return 0

    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    else:
        return 60


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # 1. Recorrência inicial dos times (Mínimo 3/5 em cada)
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0))
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))

    # 2. Métricas do padrão estatístico
    m_feitos_casa = float(s.get("mandante_gols_feitos_casa", 0) or 0)
    m_sofridos_casa = float(s.get("mandante_gols_sofridos_casa", 0) or 0)
    v_feitos_fora = float(s.get("visitante_gols_feitos_fora", 0) or 0)
    v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)

    m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)
    v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)

    media_total_confronto = (m_feitos_casa + m_sofridos_casa + v_feitos_fora + v_sofridos_fora) / 5.0

    mercados_aprovados = []

    # ----------------------------------------------------------
    # 🚨 TRAVAS DE SEGURANÇA CONTRA GOLEADAS
    # ----------------------------------------------------------
    visitante_peneira = v_sofridos_fora >= 7
    mandante_avassalador = m_feitos_casa >= 8

    # ----------------------------------------------------------
    # 🟢 OVER +1.5 GOLS
    # Libera se a média for >= 1.8 (suficiente para 2 gols) OU se o visitante for peneira
    # ----------------------------------------------------------
    if pct_15 > 0:
        if m_jogos_marcou_casa >= 3 and (v_jogos_marcou_fora >= 3 or visitante_peneira):
            if media_total_confronto >= 1.8 or mandante_avassalador:
                mercados_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})

    # ----------------------------------------------------------
    # 🟢 OVER +2.5 GOLS
    # Libera se a média for >= 2.6 OU visitante tomou 7+ gols
    # ----------------------------------------------------------
    if pct_25 > 0:
        if v_sofridos_fora >= 7 or media_total_confronto >= 2.6 or mandante_avassalador:
            mercados_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # ----------------------------------------------------------
    # 🔴 UNDERS -3.5 E -4.5
    # Só entra se NÃO houver risco de goleada e a média for estritamente baixa
    # ----------------------------------------------------------
    pode_apostar_under = not (visitante_peneira or mandante_avassalador)

    if pode_apostar_under:
        if pct_m35 > 0 and media_total_confronto <= 2.4:
            mercados_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
            
        if pct_m45 > 0 and media_total_confronto <= 2.8:
            mercados_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})

    return mercados_aprovados
    
