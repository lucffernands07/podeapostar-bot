"""
REGRAS DE GOLS - BASEADAS EXCLUSIVAMENTE NOS 4 EXEMPLOS
- Permite 3/5 com 4/5 ou 5/5 apenas quando o padrão do confronto confirma.
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    # Veta se algum tiver menos de 3/5
    if c < 3 or f < 3:
        return 0

    # Nível de confiança proporcional
    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    else:
        return 60  # Entra na regra de transição do 3/5


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # 1. Recorrência inicial dos times
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
    # 🟢 OVER +1.5 GOLS (Padrão Mirassol x Grêmio)
    # Exige eficiência de ataque ou média >= 2.2 para aceitar 3/5
    # ----------------------------------------------------------
    if pct_15 > 0:
        if m_jogos_marcou_casa >= 3 and (v_jogos_marcou_fora >= 3 or v_sofridos_fora >= 8):
            if media_total_confronto >= 2.2:
                mercados_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})

    # ----------------------------------------------------------
    # 🟢 OVER +2.5 GOLS (Padrão América de Cali x Boyacá)
    # Só aceita 3/5 se o visitante for "saco de pancadas" (v_sofridos_fora >= 9)
    # ----------------------------------------------------------
    if pct_25 > 0:
        if v_sofridos_fora >= 9 or media_total_confronto >= 3.0:
            mercados_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # ----------------------------------------------------------
    # 🔴 UNDERS -3.5 E -4.5 (Padrão Chape x Cruzeiro)
    # Veta o Under se o visitante tomar goleadas repetidas
    # ----------------------------------------------------------
    visitante_eh_pancada = v_sofridos_fora >= 10

    if not visitante_eh_pancada:
        if pct_m35 > 0 and media_total_confronto <= 2.8:
            mercados_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
            
        if pct_m45 > 0 and media_total_confronto <= 3.4:
            mercados_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})

    return mercados_aprovados
    
