"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
1. Exige aprovação prévia de QUALQUER outro mercado no jogo.
2. SIM: Visitante fora com Média de Gols >= 1.6 (últimos 5 jogos).
3. NÃO: Visitante fora com Média de Gols <= 0.8 (últimos 5 jogos).
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    """
    Avalia BTTS SIM / NÃO baseado na média de gols do visitante fora de casa,
    apenas se já houver pelo menos 1 outro mercado aprovado para o confronto.
    """
    try:
        if not isinstance(s, dict):
            return []

        # Captura os mercados aprovados enviados pelo main.py
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação estrita de presença de mercados prévios
        tem_mercado_valido = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
        elif isinstance(mercados_previos, dict):
            # Se o main mandar um dicionário como {'gols': [...], 'vitorias': [...]}, checa se há algum item nas listas
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))

        if not tem_mercado_valido:
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
        
