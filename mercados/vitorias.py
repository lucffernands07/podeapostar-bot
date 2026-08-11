"""
REGRAS DE MERCADO - VITÓRIAS (CASA / FORA)
Mercado de maior risco: exige rigor estatístico superior à Chance Dupla.
"""

def verificar_vitorias(s):
    """
    Recebe o dicionário 's' e retorna mercados de Vitórias aprovados (Vitória Casa ou Vitória Fora).
    Se ambos baterem ou se as condições não forem estritamente fortes, descarta.
    """
    mercados_aprovados = []
    if not isinstance(s, dict):
        return mercados_aprovados

    # --- CAPTURA DE DADOS COMPLEMENTARES ---
    m_vitorias_casa = int(s.get("mandante_vitorias_casa", 0) or 0)
    v_vitorias_fora = int(s.get("visitante_vitorias_fora", 0) or 0)

    v_derrotas_fora = int(s.get("visitante_derrotas_fora", 0) or 0)
    m_sem_derrota_casa = int(s.get("mandante_sem_derrota_casa", 0) or 0)
    m_derrotas_casa = 5 - m_sem_derrota_casa

    v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)
    m_sofridos_casa = float(s.get("mandante_gols_sofridos_casa", 0) or 0)

    tem_vitoria_casa = False
    tem_vitoria_fora = False

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA CADA (Nível Acima da Dupla Chance 1X)
    # Exige: Mandante com pelo menos 4 vitórias em casa (ou 100% de vitórias) 
    # E o visitante com muitas derrotas fora OU defesa extremamente vazada (>= 8 gols sofridos).
    # ----------------------------------------------------------
    condicao_vitoria_casa = (m_vitorias_casa >= 4) and (v_derrotas_fora >= 3 or v_sofridos_fora >= 8)

    if condicao_vitoria_casa:
        tem_vitoria_casa = True

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA FORA (Nível Acima da Dupla Chance X2)
    # Exige: Visitante com pelo menos 4 vitórias fora 
    # E o mandante com muitas derrotas em casa (>= 3) OU defesa extremamente vazada (>= 8 gols sofridos).
    # ----------------------------------------------------------
    condicao_vitoria_fora = (v_vitorias_fora >= 4) and (m_derrotas_casa >= 3 or m_sofridos_casa >= 8)

    if condicao_vitoria_fora:
        tem_vitoria_fora = True

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # Se os dois lados apontarem vitória seca, o jogo é inconclusivo e anula.
    # ----------------------------------------------------------
    if tem_vitoria_casa and tem_vitoria_fora:
        print(f"      ⚠️ CONFLITO DE VITÓRIAS: Vitória Casa e Vitória Fora passaram juntas. Jogo descartado.")
        return []

    if tem_vitoria_casa:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Casa", 
            "tipo": "VITORIA_CASA"
        })
    
    if tem_vitoria_fora:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Fora", 
            "tipo": "VITORIA_FORA"
        })

    return mercados_aprovados
    
