"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Ajustado para acumular os mercados em lista sem encerrar a execução prematuramente.
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Captura os mercados aprovados enviados pelo main.py
        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados

        # 🛑 TRAVA 1: Validação de presença de mercados prévios
        tem_mercado_valido = False
        tem_over_aprovado = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            tem_mercado_valido = True
            tem_over_aprovado = any("GOLS_15" in item.get("tipo", "") or "GOLS_25" in item.get("tipo", "") for item in mercados_previos if isinstance(item, dict))
        elif isinstance(mercados_previos, dict):
            tem_mercado_valido = any(len(v) > 0 for v in mercados_previos.values() if isinstance(v, list))
            lista_gols = mercados_previos.get("gols", [])
            tem_over_aprovado = any("GOLS_15" in item.get("tipo", "") or "GOLS_25" in item.get("tipo", "") for item in lista_gols if isinstance(item, dict))

        if not tem_mercado_valido:
            print("   ⚠️ BTTS BARRADO: Nenhum outro mercado foi aprovado para este jogo.")
            return []

        # Métricas detalhadas da raspagem
        media_gols_visitante = float(s.get("media_gols_fora", 0) or 0)
        v_jogos_marcou_fora = int(s.get("visitante_jogos_com_gol_fora", 0) or 0)
        mandante_sofreu_gol_ultimo = s.get("mandante_sofreu_gol_ultimo_casa", False)

        # 🟢 REGRA 1: AMBAS MARCAM SIM
        if media_gols_visitante >= 1.6 or v_jogos_marcou_fora >= 4:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA 2: AMBAS MARCAM NÃO (COM TRAVAS ANTI-RED)
            if tem_over_aprovado:
                print("   ⚠️ BTTS NÃO BARRADO: Jogo tem tendência de Over aprovada.")
            elif v_jogos_marcou_fora >= 3:
                print("   ⚠️ BTTS NÃO BARRADO: Visitante costuma marcar gols fora (>= 3/5 jogos).")
            else:
                if media_gols_visitante <= 0.6:
                    if not mandante_sofreu_gol_ultimo:
                        mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
                    else:
                        print("   ⚠️ BTTS NÃO BARRADO: Mandante sofreu gol no último jogo em casa.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
              
