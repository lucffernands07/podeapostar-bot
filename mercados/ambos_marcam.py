"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
1. Exige aprovação prévia de QUALQUER outro mercado no jogo.
2. SIM: Visitante fora com Média de Gols >= 1.6 (últimos 5 jogos).
3. NÃO: Visitante fora com Média de Gols <= 0.8 (últimos 5 jogos).
"""

def verificar_btts(s, outros_mercados_aprovados=None):
    """
    Avalia BTTS SIM / NÃO baseado na média de gols do visitante fora de casa,
    apenas se já houver pelo menos 1 outro mercado aprovado para o confronto.
    """
    try:
        if not isinstance(s, dict):
            return []

        # 🛑 TRAVA 1: Se não houver NENHUM outro mercado aprovado antes, cancela o BTTS
        if not outros_mercados_aprovados: # lista vazia ou None
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Captura a média de gols do visitante jogando fora de casa (últimos 5 jogos)
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM (Média visitante fora >= 1.6)
        if media_gols_visitante >= 1.6:
            return [{"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"}]

        # 🔴 REGRA 2: AMBAS MARCAM NÃO (Média visitante fora <= 0.8)
        if media_gols_visitante <= 0.8:
            return [{"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"}]

        return []

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return []
        
