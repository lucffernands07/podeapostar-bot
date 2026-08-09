"""
REGRAS DE MERCADO - CHANCE DUPLA (1X / X2)
O filtro 'E' estatístico é exigido globalmente para ambas as condições do 'OU'.
"""

def verificar_chance_dupla(s):
    """
    Recebe o dicionário 's' e retorna mercados de Chance Dupla aprovados (1X ou X2).
    """
    if not isinstance(s, dict):
        return []

    mercados_aprovados = []

    # --- CAPTURA DE DADOS COMPLEMENTARES ---
    m_sem_derrota_casa = int(s.get("mandante_sem_derrota_casa", 0) or 0)
    v_sem_derrota_fora = int(s.get("visitante_sem_derrota_fora", 0) or 0)

    m_vitorias_casa = int(s.get("mandante_vitorias_casa", 0) or 0)
    v_derrotas_fora = int(s.get("visitante_derrotas_fora", 0) or 0)

    v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)

    # ----------------------------------------------------------
    # 🟢 REGRA 1X (Casa ou Empate)
    # Exige (Mandante sem derrota >= 4/5 OU Visitante derrotas >= 3/5)
    # E OBRIGATORIAMENTE: Visitante levou >= 8 gols fora.
    # ----------------------------------------------------------
    condicao_1x = (m_sem_derrota_casa >= 4 or v_derrotas_fora >= 2) and (v_sofridos_fora >= 6)

    if condicao_1x:
        pct = 100 if m_sem_derrota_casa == 5 else 80
        mercados_aprovados.append({"mercado": f"Dupla Chance: 1X ({pct}%)", "tipo": "DC_1X"})

    # ----------------------------------------------------------
    # 🟢 REGRA X2 (Empate ou Visitante)
    # Exige (Visitante sem derrota >= 4/5 OU Mandante vitorias <= 1)
    # E OBRIGATORIAMENTE: Visitante pontuou >= 3/5 AND Gols sofridos <= 7.
    # ----------------------------------------------------------
    condicao_x2 = (v_sem_derrota_fora >= 4 or m_vitorias_casa <= 1) and (v_sem_derrota_fora >= 3 and v_sofridos_fora <= 7)

    if condicao_x2:
        pct = 100 if v_sem_derrota_fora == 5 else 80
        mercados_aprovados.append({"mercado": f"Dupla Chance: X2 ({pct}%)", "tipo": "DC_X2"})

    return mercados_aprovados
    
