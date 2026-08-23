"""
REGRAS DE MERCADO - AMBAS MARCAM (NOVA REGRA)
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None, odds_jogo=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        mercados_previos = outros_mercados_aprovados or mercados_gols_aprovados
        
        tem_over = False
        tem_under = False

        # Valida se tem mercado de Over ou Under ativo nos prévios
        if isinstance(mercados_previos, list) and len(mercados_previos) > 0:
            for item in mercados_previos:
                if not isinstance(item, dict):
                    continue
                tipo_upper = item.get("tipo", "").upper()
                
                if "OVER" in tipo_upper or "GOLS_15" in tipo_upper or "GOLS_25" in tipo_upper:
                    tem_over = True
                if "UNDER" in tipo_upper or "M35" in tipo_upper or "M25" in tipo_upper or "GOLS_M" in tipo_upper:
                    tem_under = True

        # Pega os dados do último jogo salvos pelo scraper
        gols_mandante_ult_casa = int(s.get("gols_mandante_ultimo_casa", 0) or 0)
        gols_adversario_ult_casa = int(s.get("gols_adversario_ultimo_casa", 0) or 0)
        
        gols_visitante_ult_fora = int(s.get("gols_visitante_ultimo_fora", 0) or 0)
        gols_adversario_ult_fora = int(s.get("gols_adversario_ultimo_fora", 0) or 0)

        # Soma total dos gols do último jogo de cada um
        total_gols_ultimos_jogos = (gols_mandante_ult_casa + gols_adversario_ult_casa) + (gols_visitante_ult_fora + gols_adversario_ult_fora)

        # Visitante não tomou gol no último jogo fora (gols do adversário contra ele = 0)
        visitante_nao_tomou_gol = (gols_adversario_ult_fora == 0)

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
        # 3. Visitante não tomou gol no último jogo (exclusivo para o NÃO)
        if tem_under and total_gols_ultimos_jogos <= 3 and visitante_nao_tomou_gol:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})
        else:
            print(f"   ⚠️ BTTS NÃO BARRADO: Under={tem_under}, Soma Gols={total_gols_ultimos_jogos} (Exige <= 3), Visitante Zero Gols Sofridos={visitante_nao_tomou_gol}")

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar nova regra Ambas Marcam: {e}")
        return mercados_aprovados
        
