"""
REGRAS DE MERCADO - AMBAS MARCAM (SIMPLIFICADO)
Sincronizado com as chaves reais do gols.py (GOLS_15, GOLS_25, GOLS_M35, GOLS_M45)
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
        tem_under_45_ativo = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            for item in mercados_previos:
                if not isinstance(item, dict):
                    continue
                tipo_upper = item.get("tipo", "").upper()
                texto_upper = item.get("mercado", "").upper()
                
                # Identifica Over ativo (GOLS_15, GOLS_25 ou similares)
                if "GOLS_15" in tipo_upper or "GOLS_25" in tipo_upper or "OVER" in tipo_upper:
                    tem_over_ativo = True
                
                # Identifica Under -3.5 (Compatível com GOLS_M35 ou texto -3.5)
                if "GOLS_M35" in tipo_upper or "M35" in tipo_upper or "3.5" in texto_upper or "-3.5" in texto_upper:
                    tem_under_35_ativo = True

                # Identifica Under -4.5 (Compatível com GOLS_M45 ou texto -4.5)
                if "GOLS_M45" in tipo_upper or "M45" in tipo_upper or "4.5" in texto_upper or "-4.5" in texto_upper:
                    tem_under_45_ativo = True
            
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            for item in lista_gols:
                if not isinstance(item, dict):
                    continue
                tipo_upper = item.get("tipo", "").upper()
                texto_upper = item.get("mercado", "").upper()
                
                if "GOLS_15" in tipo_upper or "GOLS_25" in tipo_upper or "OVER" in tipo_upper:
                    tem_over_ativo = True
                if "GOLS_M35" in tipo_upper or "M35" in tipo_upper or "3.5" in texto_upper or "-3.5" in texto_upper:
                    tem_under_35_ativo = True
                if "GOLS_M45" in tipo_upper or "M45" in tipo_upper or "4.5" in texto_upper or "-4.5" in texto_upper:
                    tem_under_45_ativo = True

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # 🟢 REGRA 1: BTTS SIM (Se tem OVER ativo)
        if tem_over_ativo:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            print("   ⚠️ BTTS SIM, BARRADO: Jogo não possui Over ativo.")

        # 🔴 REGRA 2: BTTS NÃO (Se tem UNDER -3.5 ativo e NÃO tem -4.5)
        if tem_over_ativo:
            print("   ⚠️ BTTS NÃO, BARRADO: Jogo tem Over ativo (Exclusão Mútua).")
        elif tem_under_45_ativo:
            print("   ⚠️ BTTS NÃO, BARRADO: Jogo possui linha de -4.5 Gols ativa (exige estritamente apenas -3.5).")
        elif tem_under_35_ativo:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
        else:
            print("   ⚠️ BTTS NÃO, BARRADO: O mercado de gols aprovado não é o -3.5.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
                
