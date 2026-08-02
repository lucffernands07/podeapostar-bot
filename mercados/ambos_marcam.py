"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
1. Exige aprovação prévia de QUALQUER mercado de gols.
2. SIM: Mínimo 4/5 BTTS em casa/fora.
3. NÃO: Máximo 3/5 BTTS em casa/fora + Último jogo de ambos deve ter pelo menos um time com 0 gols.
"""

def verificar_btts(s, mercados_gols_aprovados=None):
    """
    Avalia BTTS SIM / NÃO apenas se já houver pelo menos 1 mercado de gols aprovado.
    """
    try:
        if not isinstance(s, dict):
            return []

        # 🛑 TRAVA 1: Se não houver NENHUM mercado de gols aprovado antes, cancela o BTTS
        if not mercados_gols_aprovados: # lista vazia ou None
            print("   ⚠️ BTTS BARRADO: Nenhum mercado de gols foi aprovado para este jogo.")
            return []

        btts_casa = s.get("casa_btts", 0)
        btts_fora = s.get("fora_btts", 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM (Mínimo 4/5)
        if btts_casa >= 4 and btts_fora >= 4:
            if btts_casa == 5 and btts_fora == 5:
                return [{"mercado": "Ambas Marcam: Sim (100%)", "tipo": "BTTS_SIM"}]
            return [{"mercado": "Ambas Marcam: Sim (80%)", "tipo": "BTTS_SIM"}]

        # 🔴 REGRA 2: AMBAS MARCAM NÃO (Máximo 3/5)
        if btts_casa <= 3 and btts_fora <= 3:
            # Captura os últimos placares registrados para mandante e visitante
            placar_casa = s.get("t1_placar_1", "") or ""
            placar_fora = s.get("t2_placar_1", "") or ""

            # 🛑 TRAVA 2: Verifica se o último jogo de cada time teve algum zero (0 gols de alguém)
            ultimo_jogo_casa_com_zero = "0" in placar_casa
            ultimo_jogo_fora_com_zero = "0" in placar_fora

            if ultimo_jogo_casa_com_zero and ultimo_jogo_fora_com_zero:
                if btts_casa <= 1 and btts_fora <= 1:
                    return [{"mercado": "Ambas Marcam: Não (100%)", "tipo": "BTTS_NAO"}]
                return [{"mercado": "Ambas Marcam: Não (80%)", "tipo": "BTTS_NAO"}]
            else:
                print("   ⚠️ BTTS NÃO BARRADO: O último jogo de um dos times teve gols de ambos os lados.")

        return []

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return []
        
