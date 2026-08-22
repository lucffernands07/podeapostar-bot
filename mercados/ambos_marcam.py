"""
REGRAS DE MERCADO - AMBAS MARCAM (COM FILTRO DE ODD <= 1.20)
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None, odds_jogo=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados
        odds = odds_jogo or {}

        tem_mercado_valido = False
        over_valido_120 = False
        under_35_valido_120 = False
        tem_under_45_ativo = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            for item in mercados_previos:
                if not isinstance(item, dict):
                    continue
                tipo_upper = item.get("tipo", "").upper()
                texto_upper = item.get("mercado", "").upper()
                
                # Valida Over (GOLS_15 ou GOLS_25) e checa se a odd é <= 1.20
                if "GOLS_15" in tipo_upper or "GOLS_25" in tipo_upper or "OVER" in tipo_upper:
                    odd_str = odds.get(tipo_upper, "99")
                    try:
                        if float(str(odd_str).replace(',', '.')) <= 1.20:
                            over_valido_120 = True
                    except:
                        pass
                
                # Valida Under -3.5 e checa se a odd é <= 1.20
                if "GOLS_M35" in tipo_upper or "M35" in tipo_upper or "3.5" in texto_upper or "-3.5" in texto_upper:
                    odd_str = odds.get("GOLS_M35", "99")
                    try:
                        if float(str(odd_str).replace(',', '.')) <= 1.20:
                            under_35_valido_120 = True
                    except:
                        pass

                if "GOLS_M45" in tipo_upper or "M45" in tipo_upper or "4.5" in texto_upper or "-4.5" in texto_upper:
                    tem_under_45_ativo = True

        if not tem_mercado_valido:
            print("    ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # 🟢 REGRA 1: BTTS SIM (Entra se houver Over com odd <= 1.20)
        if over_valido_120:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            print("    ⚠️ BTTS SIM, BARRADO: Nenhum Over ativo possui odd <= 1.20.")

        # 🔴 REGRA 2: BTTS NÃO (Entra se o Under -3.5 tiver odd <= 1.20 e não tiver -4.5)
        if over_valido_120:
            print("    ⚠️ BTTS NÃO, BARRADO: Jogo tem Over válido (Exclusão Mútua).")
        elif tem_under_45_ativo:
            print("    ⚠️ BTTS NÃO, BARRADO: Jogo possui linha de -4.5 Gols ativa.")
        elif under_35_valido_120:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
        else:
            print("    ⚠️ BTTS NÃO, BARRADO: O mercado Under -3.5 não possui odd <= 1.20.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
