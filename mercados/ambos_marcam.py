"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Sincronizado com a Exclusão Mútua do gols.py (Over x Under).
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Captura os mercados de gols aprovados enviados pelo main.py[span_0](start_span)[span_0](end_span)
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação de presença de mercados prévios
        tem_mercado_valido = False
        tem_over_ativo = False
        tem_under_35_ativo = False # Restrito estritamente ao -3.5

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            # Identifica Over ativo
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
            
            # Identifica se o Under aprovado foi especificamente o -3.5 (M35)
            tem_under_35_ativo = any("M35" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
            
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            tem_over_ativo = any("GOLS_15" in item.get("tipo", "").upper() or "GOLS_25" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))
            tem_under_35_ativo = any("M35" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Métricas detalhadas da raspagem
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)
        v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)
        
        media_gols_mandante = float(s.get("media_gols_casa", 0) or 0)
        m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM 
        condicao_btts_sim = (
            tem_over_ativo and 
            media_gols_visitante >= 1.0 and 
            media_gols_mandante >= 0.8
        )

        if condicao_btts_sim:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA 2: AMBAS MARCAM NÃO
            # Se tem Over ativo, respeita a exclusão mútua
            if tem_over_ativo:
                print("   ⚠️ BTTS NÃO BARRADO: Jogo tem tendência de Over ativa (Exclusão Mútua respeitada).")
                return mercados_aprovados

            # 🛑 NOVA TRAVA: Se não foi aprovado estritamente o Under -3.5, barra o BTTS Não
            if not tem_under_35_ativo:
                print("   ⚠️ BTTS NÃO BARRADO: O mercado de gols aprovado não é o -3.5.")
                return mercados_aprovados

            # Se passou com Under -3.5 confirmado, avalia as frequências
            if v_jogos_marcou_fora >= 3 or m_jogos_marcou_casa >= 3:
                print("   ⚠️ BTTS NÃO BARRADO: Ambas as equipes marcam com muita frequência, mesmo com linha de Under -3.5.")
            else:
                if media_gols_visitante <= 0.8 or media_gols_mandante <= 0.8:
                    mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
                else:
                    print("   ⚠️ BTTS NÃO BARRADO: Médias intermediárias, fora do padrão estrito de Não.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
                
