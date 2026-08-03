"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Ajustado com travas anti-RED de constância de gols e integração de Over.
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    try:
        if not isinstance(s, dict):
            return []

        # Captura os mercados aprovados enviados pelo main.py
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação de presença de mercados prévios
        tem_mercado_valido = False
        tem_over_aprovado = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            # Checa se algum Over foi aprovado nos gols
            tem_over_aprovado = any("GOLS_15" in item.get("tipo", "") or "GOLS_25" in item.get("tipo", "") for item in mercados_previos if isinstance(item, dict))
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            # Checa Over dentro de dicionário
            lista_gols = mercados_previos.get("gols", [])
            tem_over_aprovado = any("GOLS_15" in item.get("tipo", "") or "GOLS_25" in item.get("tipo", "") for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Métricas detalhadas da raspagem
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)
        v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)
        v_sofridos_fora = float(s.get("visitante_gols_sofridos_fora", 0) or 0)
        mandante_sofreu_gol_ultimo = s.get("mandante_sofreu_gol_ultimo_casa", False)

        # 🟢 REGRA 1: AMBAS MARCAM SIM
        # Ativa se a média do visitante for alta (>= 1.6) OU se o visitante marca com muita constância fora (>= 4/5 jogos)
        if media_gols_visitante >= 1.6 or v_jogos_marcou_fora >= 4:
            return [{"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"}]

        # 🔴 REGRA 2: AMBAS MARCAM NÃO (COM TRAVAS ANTI-RED)
        # 1. Se o jogo já aprovou Over 1.5 ou Over 2.5, não arrisca BTTS NÃO em jogos movimentados
        if tem_over_aprovado:
            print("   ⚠️ BTTS NÃO BARRADO: Jogo tem tendência de Over aprovada.")
            return []

        # 2. Se o visitante costuma marcar gols fora (em 3 ou mais dos últimos 5 jogos), VETA o BTTS NÃO
        if v_jogos_marcou_fora >= 3:
            print("   ⚠️ BTTS NÃO BARRADO: Visitante costuma marcar gols fora (>= 3/5 jogos).")
            return []

        # 3. Média de gols do visitante bem baixa (<= 0.6) AND Mandante sem sofrer gol no último jogo
        if media_gols_visitante <= 0.6:
            if not mandante_sofreu_gol_ultimo:
                return [{"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"}]
            else:
                print("   ⚠️ BTTS NÃO BARRADO: Mandante sofreu gol no último jogo em casa.")

        return []

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return []
            
