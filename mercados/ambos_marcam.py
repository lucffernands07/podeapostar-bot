"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Sincronizado com a Exclusão Mútua do gols.py (Over x Under).
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Captura os mercados de gols aprovados enviados pelo main.py (oriundos do gols.py)[span_3](start_span)[span_3](end_span)[span_4](start_span)[span_4](end_span)
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação de presença de mercados prévios
        tem_mercado_valido = False
        tem_over_ativo = False
        tem_under_ativo = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            # Identifica se o gols.py aprovou Over ou Under com base no tipo retornado
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
            tem_under_ativo = any("M35" in item.get("tipo", "").upper() or "M45" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))
            tem_under_ativo = any("M35" in item.get("tipo", "").upper() or "M45" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Métricas detalhadas da raspagem[span_5](start_span)[span_5](end_span)
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)
        v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)
        
        media_gols_mandante = float(s.get("media_gols_casa", 0) or 0)
        m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM 
        # Só é avaliado se o jogo teve Over aprovado no gols.py e médias fortes de ambos
        condicao_btts_sim = (
            tem_over_ativo and 
            media_gols_visitante >= 1.2 and 
            media_gols_mandante >= 1.0
        )

        if condicao_btts_sim:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA 2: AMBAS MARCAM NÃO
            # Se o gols.py aprovou um UNDER (ex: -3.5 ou -4.5), o BTTS Não ganha coerência e pode ser validado pelas médias
            if tem_over_ativo:
                print("   ⚠️ BTTS NÃO BARRADO: Jogo tem tendência de Over ativa (Exclusão Mútua respeitada).")
                return mercados_aprovados

            # Se passou em Under, avalia as travas de frequência para soltar o "Não" com segurança
            if v_jogos_marcou_fora >= 3 or m_jogos_marcou_casa >= 3:
                print("   ⚠️ BTTS NÃO BARRADO: Ambas as equipes marcam com muita frequência, mesmo com linha de Under.")
            else:
                if media_gols_visitante <= 0.8 or media_gols_mandante <= 0.8:
                    mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
                else:
                    print("   ⚠️ BTTS NÃO BARRADO: Médias intermediárias, fora do padrão estrito de Não.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
        
