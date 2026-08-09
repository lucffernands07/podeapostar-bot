"""
REGRAS DE MERCADO - AMBAS MARCAM (SIMPLIFICADO)
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Captura os mercados de gols aprovados enviados pelo main.py
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        tem_mercado_valido = False
        tem_over_ativo = False
        tem_under_35_ativo = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
            tem_under_35_ativo = any("M35" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
            
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))
            tem_under_35_ativo = any("M35" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # 🟢 REGRA 1: BTTS SIM (Se tem OVER ativo)
        if tem_over_ativo:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            print("   ⚠️ BTTS SIM, BARRADO: Jogo não possui Over ativo.")

        # 🔴 REGRA 2: BTTS NÃO (Se tem UNDER com gols -3.5)
        if tem_over_ativo:
            print("   ⚠️ BTTS NÃO, BARRADO: Jogo tem Over ativo (Exclusão Mútua).")
        elif tem_under_35_ativo:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
        else:
            print("   ⚠️ BTTS NÃO, BARRADO: O mercado de gols aprovado não é o -3.5.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
            
