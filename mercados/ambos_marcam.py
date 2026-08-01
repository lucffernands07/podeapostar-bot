"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
1. Exige aprovação prévia de QUALQUER mercado de gols.
2. SIM: Mínimo 4/5 BTTS em casa/fora.
3. NÃO: Máximo 3/5 BTTS em casa/fora.
"""

def verificar_btts(s, mercados_gols_aprovados=None):
    """
    Avalia BTTS SIM / NÃO apenas se já houver pelo menos 1 mercado de gols aprovado.
    """
    try:
        if not isinstance(s, dict):
            return []

        # 🛑 TRAVA: Se não houver NENHUM mercado de gols aprovado antes, cancela o BTTS
        if not mercados_gols_aprovados: # lista vazia ou None
            print("   ⚠️ BTTS BARRADO: Nenhum mercado de gols foi aprovado para este jogo.")
            return []

        btts_casa = s.get("casa_btts", 0)
        btts_fora = s.get("fora_btts", 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM (Mínimo 4/5)
        if btts_casa >= 4 and btts_fora >= 4:
            if btts_casa == 5 and btts_fora == 5:
                return ["Ambas Marcam: Sim (100%)"]
            return ["Ambas Marcam: Sim (80%)"]

        # 🔴 REGRA 2: AMBAS MARCAM NÃO (Máximo 3/5)
        if btts_casa <= 3 and btts_fora <= 3:
            if btts_casa <= 1 and btts_fora <= 1:
                return ["Ambas Marcam: Não (100%)"]
            return ["Ambas Marcam: Não (80%)"]

        return []

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return []
        
