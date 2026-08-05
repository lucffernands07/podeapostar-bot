"""
REGRAS DE MERCADO - AMBAS MARCAM (BTTS SIM / NÃO)
Ajustado para acumular os mercados em lista e equilibrar a aparição de Sim e Não.
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
        
        media_gols_mandante = float(s.get("media_gols_casa", 0) or 0)
        m_jogos_marcou_casa = int(s.get("mandante_jogos_com_gol_casa", 0) or 0)
        
        mandante_sofreu_gol_ultimo = s.get("mandante_sofreu_gol_ultimo_casa", False)

        # 🟢 REGRA 1: AMBAS MARCAM SIM (Atualizada com as 3 novas regras em sequência)
        condicao_btts_sim = (
            tem_over_aprovado and 
            media_gols_visitante >= 1.5 and 
            media_gols_mandante >= 1.0
        )

        if condicao_btts_sim:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA 2: AMBAS MARCAM NÃO (Mantida exatamente como estava antes)
            if tem_over_aprovado:
                print("   ⚠️ BTTS NÃO BARRADO: Jogo tem tendência de Over aprovada.")
            elif v_jogos_marcou_fora >= 4 or m_jogos_marcou_casa >= 4:
                print("   ⚠️ BTTS NÃO BARRADO: Ambas as equipes marcam com muita frequência.")
            else:
                if media_gols_visitante <= 0.9 or media_gols_mandante <= 0.9:
                    mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
                else:
                    print("   ⚠️ BTTS NÃO BARRADO: Médias intermediárias, fora do padrão estrito de Não.")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return mercados_aprovados
            
