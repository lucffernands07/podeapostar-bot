"""
REGRAS DE MERCADO - AMBAS MARCAM (LENDO PLACARES JÁ EXISTENTES)
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None, odds_jogo=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados
        
        tem_over = False
        tem_under = False

        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            for item in mercados_previos:
                if not isinstance(item, dict):
                    continue
                tipo_upper = item.get("tipo", "").upper()
                
                if "OVER" in tipo_upper or "GOLS_15" in tipo_upper or "GOLS_25" in tipo_upper:
                    tem_over = True
                if "UNDER" in tipo_upper or "M35" in tipo_upper or "M25" in tipo_upper or "GOLS_M" in tipo_upper:
                    tem_under = True

        # Lê os placares do último jogo que o raspagem_h2h.py já salva
        placar_mandante_casa = s.get("t1_placar_1", "")  # Ex: "2-1[span_3](start_span)"[span_3](end_span)
        placar_visitante_fora = s.get("t2_placar_1", "") # Ex: "0-2[span_4](start_span)"[span_4](end_span)

        gols_m_casa, gols_adv_casa = 0, 0
        gols_adv_fora, gols_v_fora = 0, 0

        # Quebra o placar do mandante (casa)
        if placar_mandante_casa and "-" in placar_mandante_casa:
            partes = placar_mandante_casa.split("-")
            gols_m_casa = int(partes[0].strip())
            gols_adv_casa = int(partes[1].strip())

        # Quebra o placar do visitante (fora)
        if placar_visitante_fora and "-" in placar_visitante_fora:
            partes = placar_visitante_fora.split("-")
            gols_adv_fora = int(partes[0].strip()) # Gols que o mandante/adversário fez nele
            gols_v_fora = int(partes[1].strip())   # Gols que o visitante fez

        # Soma total dos gols do último jogo de cada um
        total_gols_ultimos_jogos = (gols_m_casa + gols_adv_casa) + (gols_adv_fora + gols_v_fora)

        # Regra exclusiva para o NÃO: Visitante não tomou gol no último jogo (gols do adversário contra ele = 0)
        visitante_nao_tomou_gol = (gols_adv_fora == 0)

        # 🟢 REGRA BTTS SIM:
        # 1. Ter over
        # 2. Total de gols somados do último jogo de cada >= 7
        if tem_over and total_gols_ultimos_jogos >= 7:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            print(f"   ⚠️ BTTS SIM BARRADO: Over={tem_over}, Soma Gols Últimos Jogos={total_gols_ultimos_jogos} (Exige >= 7)")

        # 🔴 REGRA BTTS NÃO:
        # 1. Ter under
        # 2. Total de gols somados do último jogo de cada <= 3
        # 3. Visitante não tomou gol no último jogo
        if tem_under and total_gols_ultimos_jogos <= 3 and visitante_nao_tomou_gol:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
        else:
            print(f"   ⚠️ BTTS NÃO BARRADO: Under={tem_under}, Soma Gols={total_gols_ultimos_jogos} (Exige <= 3), Visitante Zero Gols Sofridos={visitante_nao_tomou_gol}")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar nova regra Ambas Marcam: {e}")
        return mercados_aprovados
                    
