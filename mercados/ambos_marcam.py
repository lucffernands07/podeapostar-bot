"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Ajustado para reconhecer qualquer mercado de gols prévio de forma ampla.
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Captura os mercados aprovados enviados pelo main.py
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação de presença de mercados prévios e detecção ampla de gols
        tem_mercado_valido = False
        tem_mercado_gols_ativo = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            # Varre qualquer tipo que tenha relação com gols (ex: GOLS_15, GOLS_25, GOLS_35_MENOS, etc.)
            tem_mercado_gols_ativo = any("GOL" in item.get("tipo", "").upper() for item in mercados_previos if isinstance(item, dict))
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            tem_mercado_gols_ativo = any("GOL" in item.get("tipo", "").upper() for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Métricas detalhadas da raspagem
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)
        v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)
        
        media_gols_mandante = float(s.get("media_gols_casa", 0) or 0)
        m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)

        # 🟢 REGRA 1: AMBAS MARCAM SIM 
        # Exige que haja um mercado de gols ativo e médias fortes de ambos os lados
        condicao_btts_sim = (
            tem_mercado_gols_ativo and 
            media_gols_visitante >= 1.2 and 
            media_gols_mandante >= 1.0
        )

        if condicao_btts_sim:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA 2: AMBAS MARCAM NÃO
            # Se houver mercado de gols ativo com forte tendência, barra o "Não" para evitar conflito
            if tem_mercado_gols_ativo:
                print("   ⚠️ BTTS NÃO BARRADO: Jogo possui mercado de gols validado, conflitando com o padrão de Não.")
            elif v_jogos_marcou_fora >= 3 or m_jogos_marcou_casa >= 3:
                print("   ⚠️ BTTS NÃO BARRADO: Ambas as equipes marcam com muita frequência.")
            else:
                if media_gols_visitante <= 0.8 or media_gols_mandante <= 0.8:
                    mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
                else:
                    print("   ⚠️ BTTS NÃO BARRADO: Médias intermediárias, fora do padrão estrito de Não.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
