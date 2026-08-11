"""
REGRAS DE MERCADO - CHANCE DUPLA (1X / X2)
O filtro 'E' estatístico é exigido globalmente para ambas as condições do 'OU'.
Com regra de descarte mútuo: se ambos passarem, os dois são eliminados.
"""

def verificar_chance_dupla(s):
    """
    Recebe o dicionário 's' e retorna mercados de Chance Dupla aprovados (1X ou X2).
    Se ambos forem verdadeiros, ambos são descartados.
    """
    if not isinstance(s, dict):
        return []

    # --- CAPTURA DE DADOS COMPLEMENTARES ---
    m_sem_derrota_casa = int(s.get("mandante_sem_derrota_casa", 0) or 0)
    v_sem_derrota_fora = int(s.get("visitante_sem_derrota_fora", 0) or 0)

    v_derrotas_fora = int(s.get("visitante_derrotas_fora", 0) or 0)
    v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)
    
    m_sofridos_casa = float(s.get("mandante_gols_sofridos_casa", 0) or 0)

    # Variáveis de controle para testar cada lado de forma independente
    tem_1x = False
    tem_x2 = False
    pct_1x = 80
    pct_x2 = 80

    # ----------------------------------------------------------
    # 🟢 REGRA 1X (Casa ou Empate)
    # ----------------------------------------------------------
    condicao_1x = (m_sem_derrota_casa >= 4 or v_derrotas_fora >= 3) and (v_sofridos_fora >= 7)

    if condicao_1x:
        tem_1x = True
        pct_1x = 100 if m_sem_derrota_casa == 5 else 80

    # ----------------------------------------------------------
    # 🟢 REGRA X2 (Invertida espelhando exatamente a lógica do 1X)
    # ----------------------------------------------------------
    m_derrotas_casa = 5 - m_sem_derrota_casa
    condicao_x2 = (v_sem_derrota_fora >= 4 or m_derrotas_casa >= 3) and (m_sofridos_casa >= 7)

    if condicao_x2:
        tem_x2 = True
        pct_x2 = 100 if v_sem_derrota_fora == 5 else 80

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # Se os dois baterem no mesmo jogo, anula os dois (retorna vazio).
    # ----------------------------------------------------------
    if tem_1x and tem_x2:
        print(f"      ⚠️ CONFLITO DE CHANCE DUPLA: 1X e X2 passaram juntos. Jogo descartado para Chance Dupla.")
        return []

    # Se apenas um passou, adiciona ele normalmente à lista
    mercados_aprovados = []
    if tem_1x:
        mercados_aprovados.append({"mercado": f"Dupla Chance: 1X ({pct_1x}%)", "tipo": "DC_1X"})
    if tem_x2:
        mercados_aprovados.append({"mercado": f"Dupla Chance: X2 ({pct_x2}%)", "tipo": "DC_X2"})

    return mercados_aprovados
    
